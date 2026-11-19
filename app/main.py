"""HTTP boundary: user-supplied BYOK credentials are request-scoped only."""
import json
from pathlib import Path

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse

from .core import MAX_BYTES, analyze, parse_docx, validate_rules

app = FastAPI(title="DocumentGuard AI", version="1.1.0", docs_url=None, redoc_url=None)
STATIC = Path(__file__).parent / "static"

@app.middleware("http")
async def no_store_analysis(request, call_next):
    response = await call_next(request)
    if request.url.path == "/api/analyze":
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["Pragma"] = "no-cache"
    return response


@app.get("/")
def home():
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-store", "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'", "Referrer-Policy": "no-referrer", "X-Content-Type-Options": "nosniff"})


@app.get("/health")
def health():
    return {"status": "ok", "auth": "bring-your-own-key", "engine": "semantic-ai"}


@app.post("/api/analyze")
async def analyze_file(
    file: UploadFile = File(...),
    rules: str = Form(...),
    authorization: str | None = Header(default=None),
):
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, "Only .docx files are supported")
    # Never echo the user's key, document text, provider exception or request body.
    api_key = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
    if not api_key or not api_key.startswith("sk-") or len(api_key) < 16 or len(api_key) > 512 or any(c.isspace() for c in api_key):
        raise HTTPException(400, "Enter a valid OpenAI API key to analyze this document")
    try:
        parsed_rules = validate_rules(json.loads(rules))
        data = await file.read(MAX_BYTES + 1)
        blocks = parse_docx(data)
        if not blocks:
            raise ValueError("Document has no readable text")
    except (ValueError, json.JSONDecodeError) as exc:
        # Validation messages originate in deterministic local code.
        raise HTTPException(400, str(exc)) from None
    try:
        return analyze(blocks, parsed_rules, api_key=api_key)
    except Exception:
        # Provider errors may contain key/request data. Never propagate them.
        raise HTTPException(502, "Analysis could not complete. Check your API key and provider access, then retry.") from None
