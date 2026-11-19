# Product Planning Conversation

**DocumentGuard AI · AI-assisted product planning**

A formatted planning dialogue covering architecture, evidence grounding, prompts, security, UX, testing, and delivery.

---

### 👤 You

> I want to build DocumentGuard AI as an evidence-first DOCX compliance reviewer. This should not be a generic chatbot or a keyword scanner. Users must define arbitrary rules in natural language, and every finding must include an exact source quote and location.

### ✦ ChatGPT

> I recommend a stateless FastAPI architecture: DOCX extraction, semantic candidate detection, deterministic evidence validation, skeptical second-pass verification, and a reviewer-facing UI with JSON export.

---

### 👤 You

> Before implementation, establish the trust boundaries. The LLM can interpret semantics, but deterministic checks must live in code. Assign stable block IDs to paragraphs and table cells, and preserve source traceability end to end.

### ✦ ChatGPT

> Agreed. Paragraphs and table cells receive identifiers such as p1 and t1r2c3. The model returns rule_id, block_id, quote, and explanation. The backend validates references and exact quotations before accepting a candidate.

---

### 👤 You

> Separate the prompts into two roles: candidate generation and independent verification. Both should treat document text as untrusted data. The second reviewer must challenge negation, examples, speculation, and hypothetical statements.

### ✦ ChatGPT

> I will implement SYSTEM_PROMPT for plausible violation detection and VERIFY_PROMPT for skeptical reassessment. Verification returns confirmed, uncertain, or rejected, with a short reason.

---

### 👤 You

> Prompting alone is not a guardrail. Reject unknown rule IDs, unknown block IDs, and quotations that are not exact contiguous substrings of the source block. Deduplicate identical findings and count rejected candidates.

### ✦ ChatGPT

> The validation layer will enforce these checks before second-pass verification. Confirmed results map to evidence_verified; uncertain results map to needs_human_review; rejected results are excluded.

---

### 👤 You

> Be precise with the claims. Exact quotation validates provenance, not semantic correctness. A second model pass is another judgment, not a mathematical proof. Zero findings cannot be presented as a guarantee of compliance.

### ✦ ChatGPT

> Understood. I will distinguish evidence grounding from semantic accuracy, preserve uncertainty, and document recall and false-negative limitations.

---

### 👤 You

> Implement BYOK. No API key in GitHub, no shared server-side secret, and no persistence in localStorage or a database. Keep the customer key in browser memory for the page session and pass it only with the analysis request.

### ✦ ChatGPT

> The UI will use a password input and an in-memory key variable. FastAPI will construct a request-scoped OpenAI client. Provider errors will be sanitized. The key and document still transit the hosting platform and OpenAI.

---

### 👤 You

> Use a configurable model, starting with gpt-4.1-mini. Request JSON objects and temperature zero, but do not call the model deterministic. Add bounded processing, explicit timeouts, and no hidden retries.

### ✦ ChatGPT

> The implementation will use OpenAI Chat Completions, JSON object responses, temperature=0, 35-block batches, a 25-second timeout, and zero automatic retries. Model cost and latency remain evaluation items.

---

### 👤 You

> Make the product usable in the first minute. Clean white interface, minimal visual noise, and a clear workflow: connect key, upload DOCX, define rules, run analysis, inspect evidence, export findings.

### ✦ ChatGPT

> I will build a responsive interface with a key modal, upload control, editable rules, status feedback, evidence cards, and JSON export.

---

### 👤 You

> I want layered QA, not just unit tests. Cover malformed DOCX files, upload limits, rule validation, fabricated quotes, duplicates, verifier decisions, API key handling, and browser-to-FastAPI E2E.

### ✦ ChatGPT

> The test suite will cover core logic, API behavior, security regressions, and Chromium E2E. OpenAI responses are mocked in automated tests, so these tests validate application behavior rather than live-model accuracy.

---

### 👤 You

> The README is the reviewer experience. Add a short product explanation, an architecture diagram, a sample document, one-click prompt documentation, test commands, and honest limitations. Verify every link.

### ✦ ChatGPT

> I will structure the repository around README.md and dedicated architecture, prompts, testing, and engineering documentation, with a sample DOCX for evaluation.

---

### 👤 You

> The hosted live demo is not reliable. Remove the link from the reviewer-facing README. Replace the animated walkthrough with a static product mockup. Do not imply that the mockup is a live model result.

### ✦ ChatGPT

> I will update the README to prioritize local setup and a static product preview while preserving direct links to source code, tests, prompts, and the sample file.

---

### 👤 You

> For final delivery, reconcile code, documentation, and QA claims. Make clear what is implemented versus what remains unverified, especially live-model precision/recall, provider behavior, production governance, and observability.

### ✦ ChatGPT

> The delivered repository includes the application, BYOK flow, source-grounded findings, second-pass verification, and documentation. The recorded automated suite reports 28 passing tests with mocked provider responses; live-model accuracy was not established.

---
