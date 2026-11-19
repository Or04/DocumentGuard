# BYOK security and release checklist

## Implemented application protections

- OpenAI key is entered through a password field and retained in a JavaScript variable for the current page session, not in localStorage or the application's database.
- The browser sends the key only in the HTTPS request `Authorization: Bearer ...` header to `POST /api/analyze`, never in the multipart form body or query string.
- FastAPI uses the key only to instantiate a request-scoped OpenAI client. Provider exception details are not returned to the browser.
- Analysis responses carry `Cache-Control: no-store, private` and `Pragma: no-cache`.
- Automated canary tests cover absence of key material in local app logs and responses, error handling, and rejection of the legacy multipart `api_key` field.

## Important trust boundaries

**This is not zero-knowledge key handling.** The browser, Vercel infrastructure, FastAPI runtime, and OpenAI client necessarily process the credential. A malicious browser extension, compromised client, application code, infrastructure component, or diagnostic tool could expose it. `Authorization` headers are not automatically guaranteed to be absent from every reverse-proxy, APM, tracing, or custom log. Avoid logging request headers, request bodies, exception locals, OpenAI SDK objects, and document text.

The uploaded document is processed by the hosting platform and OpenAI. Users must review the data-processing and retention terms before submitting sensitive documents.

## Verification completed on 2026-11-19

- 31 local tests passed with `CHROMIUM_PATH=/usr/bin/chromium pytest -q`, including real Chromium UI and browser-to-FastAPI flows with the external OpenAI provider mocked.
- Vercel project `documentguard-ai` was inspected: its latest listed production deployment is older than the security changes; project metadata indicated `live: false`.
- No runtime logs were returned for the queried 50-minute window. No project-scoped log drains were found. Neither result proves a platform-wide guarantee against credential logging.

## Production release gates (not yet satisfied)

1. Deploy the exact tested Git commit and confirm the production URL is accessible.
2. Run a **synthetic fake-key** request against the deployed endpoint (do not use a real credential) and inspect available runtime logs, drains, tracing, and error reporting for the canary.
3. Confirm no third-party integration, proxy, APM, or custom logger records `Authorization` or request bodies. Configure redaction or disable unsafe collection at the source.
4. Validate OpenAI authentication and inference using an authorized disposable key, rotate it after the test, and review provider retention settings.
5. Run CI and hosted browser E2E against the deployed revision. Keep customer credentials out of screenshots, traces, HAR files, and test artifacts.
6. Consider stronger CSP (remove `unsafe-inline` by externalizing scripts), rate limiting, access controls, abuse protection, and a production secret-management policy.

**Security status:** local application-boundary tests pass; deployment/infrastructure security is **not yet verified**.
