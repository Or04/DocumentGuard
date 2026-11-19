# System architecture & trust boundaries

## Execution path

```mermaid
sequenceDiagram
  participant B as Browser (memory key)
  participant A as FastAPI
  participant D as DOCX Parser
  participant P as OpenAI
  B->>B: User enters key in modal (password field)
  B->>B: Clear input; retain key in JS closure only
  B->>A: POST file, rules, api_key over HTTPS
  A->>A: Validate key format, MIME extension, rules, size
  A->>D: Extract plain text blocks with IDs and locations
  D-->>A: paragraphs + tables
  A->>P: Chat completion: rules + untrusted source chunks (using provided key)
  P-->>A: candidate findings (structured JSON)
  A->>A: Exact quote substring and ID validation
  A->>P: Second skeptical review per valid candidate
  P-->>A: confirmed / uncertain / rejected
  A-->>B: Evidence-backed findings; NEVER include key
  B->>B: Render with textContent; allow JSON export
```

## Components

- **Browser**: DOCX picker, rule editor, BYOK modal, status, evidence cards, JSON export. Key is a closure variable, not localStorage/sessionStorage/cookie/URL. The input is cleared after connect. Reconnect disconnects the existing key; refresh erases it. Browser memory can still be exposed by malicious extensions/XSS or compromised clients; there is no absolute guarantee of secrecy.
- **API**: receives a multipart body via `POST /api/analyze`. API keys are not placed in headers visible to browser URL/query logs and are not reflected in responses. Response uses `Cache-Control: no-store` at the HTML endpoint; do not log multipart request bodies. Provider errors are sanitized. Request-scoped key is held by the server process during the request, not persisted by application code.
- **Parser**: `python-docx`, paragraphs and tables; ZIP entry count/extracted size checks, 5 MB upload cap, 1,200 text block cap. Table cells have row/column coordinates.
- **AI**: English natural-language rules, source blocks in chunks of 35, temperature 0, JSON object output. Any rule can be expressed within size limits, but not every rule is guaranteed to be interpreted reliably. Configurable `OPENAI_MODEL` (default `gpt-4.1-mini`).
- **Validator**: only recognized rule IDs, block IDs and verbatim contiguous source quotes are accepted; duplicate evidence is removed. This is deterministic evidence grounding, not a deterministic semantic truth test.
- **Independent AI review**: second LLM evaluation of each accepted candidate. `confirmed` displays `evidence_verified`; `uncertain` displays `needs_human_review`; `rejected` is excluded. This reviewer is not truly independent evidence because both passes use the same family/model by default.

## Trust boundaries & abuse cases

| Boundary | Mitigation | Residual limitation |
|---|---|---|
| DOCX → parser | ZIP checks, XML extraction limits, no macros executed | Parser bugs, complex Word features |
| DOCX → LLM | Document treated as untrusted data in system prompt; exact quote validation | Prompt injection may still change model behavior; missed violations |
| LLM → result | Validate quote, block, rule, then skeptical review | Semantically incorrect but verbatim finding may pass |
| Browser → API key | Per-request, HTTPS in production, password field, no persistent browser storage | Compromised client/extension; platform tracing outside app control |
| API → provider | Key used only by provider client; generic error responses | Provider processes document/rules under its retention and billing policies |
| Result → DOM | `textContent` only; never inject findings as HTML | Browser extensions and other page compromises remain possible |

## Reliability and scaling

Current design favors a legible take-home implementation, not a multi-tenant regulated service. A single request performs serial chunk reviews and serial second-pass checks; the total latency and cost grow with document size and number of candidate findings. For larger documents add chunk-level concurrency with explicit cost/rate caps, background jobs, cancellation, retries with idempotency and result caching (taking confidentiality into account). In production add tenant auth, quotas, monitoring, safe logging, DLP, incident response and evaluation suites.

## Security invariant

There is **no baked-in key, no shared key, no server environment key fallback**, and no key in the Git repository. The optional standalone CLI agent skill reads `OPENAI_API_KEY` from its process environment; this is separate from the web application's BYOK path.
