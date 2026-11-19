# Engineering decisions

1. **FastAPI + python-docx + static client**: minimal setup, transparent file processing and easy local execution. Web API is stateless.
2. **User-owned keys (BYOK)**: customers supply OpenAI keys during each browser session. The server never reads a global key for the web app. This avoids vendor-side key provisioning but makes the customer's provider account bear cost and data-processing responsibilities.
3. **LLM semantic analysis**: arbitrary English natural-language policies need context reasoning, including negation and hypotheticals. Regex is not a substitute. There is **no demo analysis mode**.
4. **Deterministic quote grounding**: candidate `(rule_id, block_id, quote)` must be anchored to an existing rule and contiguous source span. This rejects fabricated quotes, not semantically wrong interpretations.
5. **Second-pass AI review**: a skeptical reviewer categorizes each grounded candidate. Rejected findings disappear, uncertain ones are flagged. Because a model still decides, this is not full determinism or independent ground truth.
6. **Untrusted document boundary**: both prompts warn that DOCX text is data, not instructions. The result DOM uses safe text nodes, never `innerHTML` with LLM output.
7. **Safe failures**: explicit input limits; no stored documents; generic provider error responses; no request logging in application code.
8. **Local browser and API tests**: integration mocked at the AI boundary so tests are deterministic and require no paid credentials. Live-provider evaluation remains an explicit release gate.

## User-visible behavior

The client can connect, replace or disconnect a key without seeing its full or partial value after saving. It is cleared from the modal input and held only in JS closure memory. After refresh it must be entered again. Upload and rule validation occur before server-side model calls.

## Known gaps

Headers/footers, charts, embedded files, images, and text boxes are outside the parser's verified extraction scope; documents requiring these need a more extensive extraction pipeline. Request concurrency and provider calls can exceed short serverless time budgets. No tenant accounts, durable audit logs, queue, billing controls, legal compliance guarantees or user-level access controls exist. Sensitive real-world deployments should implement these before customer use.
