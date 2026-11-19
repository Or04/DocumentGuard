# Quality assurance report

Execution date: **2026-11-19** · Candidate: DocumentGuard AI BYOK · Tests are local to this code revision.

## Actual verified test results

**27 passed** in `pytest -q` with system Chromium (`CHROMIUM_PATH=/usr/bin/chromium`). No skips at this run. Tests cover:

- DOCX extraction, corrupt/oversized inputs, tables, rules and bounds.
- Rule/block/quote grounding; rejection of hallucinated evidence; deduplication.
- Model orchestration with stubbed OpenAI responses: confirmed, uncertain, rejected and hallucinated scenarios.
- API upload, form validation, absence/invalid format of BYOK credentials, error sanitization, request-scoped key handoff and zero key reflection.
- Actual Chromium UI journey: no key → connect fake key → DOCX upload → intercept AI HTTP response → render evidence → download JSON → disconnect. This test **does not** invoke OpenAI; it runs the actual browser interface and its request-handling code with a simulated AI response.

Run:

```bash
pip install -r requirements-dev.txt
CHROMIUM_PATH=/usr/bin/chromium pytest -q
```

On GitHub Actions, install Chromium with `python -m playwright install --with-deps chromium`, then `pytest -q`. A successful local run is **not** evidence that GitHub Actions or a deployed Vercel app passed.

## Not yet verified

- **Live provider**: No actual OpenAI key was available; no real model inference, billing, rate limit, authentication or precision/recall evaluation has been run.
- **Hosted production E2E**: A real deployed Vercel revision must be checked with a browser and a customer-owned key. Local Chromium was successful with a routed/mocked response.
- **Business quality**: No labeled benchmark corpus, recall, precision or calibration report; no red-team prompt injection campaign; no high-load or reliability assessment.
- **Operational security**: Platform log configuration, provider data-retention policy, customer identity boundaries and penetration testing are outside this local test scope.

## Release gates

Before approving a *customer production rollout*, verify deployment corresponds to the exact tested commit, GitHub Actions passes, live OpenAI integration works with an authorized customer-owned key, exported evidence references match an approved sample document, invalid credentials produce no leakage, and compliance reviewers accept expected false-positive/false-negative rates.

## Interpreting findings

`evidence_verified` means an exact quote was verified against a parsed source block **and** a second AI reviewer accepted its relevance. It does not mean the finding is legally or technically proven. `needs_human_review` signals uncertainty. No findings does **not** prove the document is clean.
