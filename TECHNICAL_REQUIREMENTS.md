# EDB Primary Education Agent Technical Requirements

## 1. Document purpose

This document defines the functional, technical, quality, and acceptance requirements for a small working agent grounded in public Hong Kong Education Bureau information about primary education.

The project is primarily a practice exercise. It should nevertheless remain runnable, testable, and explainable within the original assessment timebox of approximately 8–12 hours. If the project is later submitted or published, the accompanying technical note must accurately disclose which parts were drafted with AI assistance and which decisions or changes were made by the developer.

## 2. Product objective

Build a web application that allows a parent or teacher to:

1. Ask questions about primary education using a controlled set of public EDB pages.
2. Receive an answer supported by retrieved source text and a visible citation.
3. Receive an explicit out-of-scope response when the source material does not support an answer.
4. Manually check the watched pages for content changes.
5. Review a readable description of detected changes.
6. Send a change notification through a configurable webhook.

The application must demonstrate genuine tool use by an LLM agent. It must not be implemented as a single unrestricted prompt containing copied page text.

## 3. Users and primary use cases

### 3.1 Parent or teacher

- Ask a factual question covered by the watched EDB pages.
- Open the cited EDB page to verify the answer.
- Ask a question not covered by the sources and receive a clear refusal rather than a guess.

### 3.2 Reviewer or developer

- See which agent tool was called for a question.
- Trigger a refresh without waiting for a scheduled job.
- Modify a local test snapshot and verify that the next check detects the change.
- Inspect the before-and-after text and the notification result.
- Run the application locally by following the README.

## 4. Source scope

### 4.1 Seed source

- Hong Kong Education Bureau primary education page:
  - https://www.edb.gov.hk/tc/edu-system/primary-secondary/primary.html

### 4.2 Allowed pages

- The seed page itself.
- First-level pages linked from the primary content section of the seed page.
- Only public HTTP or HTTPS pages that are clearly related to primary education.
- The initial crawl scope must be persisted as a configurable allowlist so that a reviewer can see exactly which URLs are used.

### 4.3 Excluded pages

- Links found only in global navigation, headers, footers, search suggestions, or unrelated site menus.
- Second-level and deeper recursive links unless explicitly added to the allowlist.
- Pages behind authentication or access controls.
- Third-party pages, downloads, and PDFs unless explicitly approved as an extension.
- Any source containing non-public or personal information.

### 4.4 Crawl behaviour

- Requests must use a descriptive user agent.
- Fetched content must be cached locally.
- A manual refresh must not repeatedly fetch the same URL within a configurable minimum interval unless test mode is enabled.
- The crawler must use conservative timeouts and must not attempt to bypass access controls.
- One failed page must not make already cached pages unavailable for Q&A.

## 5. Functional requirements

Priority definitions:

- **Must**: required for the practice project to be considered complete.
- **Should**: desirable if the Must requirements are stable.
- **Could**: extension work outside the initial timebox.

### FR-001 Source discovery and allowlist

**Priority:** Must

The system shall extract first-level primary-content links from the seed page and present or persist the final URL allowlist.

**Acceptance criteria:**

- The stored allowlist contains the seed URL and only approved direct content links.
- Global navigation and footer links are excluded.
- Duplicate and fragment-only URLs are removed.
- The URL list can be inspected without reading application source code.

### FR-002 Content extraction and normalization

**Priority:** Must

The system shall convert each watched page into a stable text representation suitable for retrieval and change comparison.

**Acceptance criteria:**

- Page title, section headings, paragraph text, source URL, fetch timestamp, and content hash are retained.
- Scripts, styles, navigation, footer text, cookie messages, and repeated boilerplate are excluded where practical.
- Whitespace and Unicode are normalized before hashing.
- A transient timestamp or layout-only change does not create a content alert.
- Traditional Chinese text remains readable after extraction.

### FR-003 Local cache and snapshots

**Priority:** Must

The system shall store the latest successful normalized snapshot locally.

**Acceptance criteria:**

- Cached content is available after an application restart.
- Each page has a URL, title, normalized content, content hash, and last successful fetch time.
- A failed refresh does not overwrite the last known good snapshot.
- The snapshot format is human-inspectable, such as JSON files or SQLite records.

### FR-004 Retrieval tool

**Priority:** Must

The agent shall have a custom tool named conceptually `search_edb_sources` that retrieves relevant source passages for a user question.

**Inputs:**

- User query.
- Optional maximum result count.

**Outputs:**

- Relevant passages.
- Page title.
- Section heading when available.
- Canonical URL.
- Retrieval score or rank.

**Acceptance criteria:**

- The tool operates only on cached allowlisted EDB content.
- Retrieved results retain citation metadata.
- A tool invocation is recorded in a visible trace or structured log.
- Empty retrieval results are represented explicitly rather than fabricated.

### FR-005 Grounded question answering

**Priority:** Must

The agent shall answer questions using only evidence returned by the retrieval tool.

**Acceptance criteria:**

- Every factual answer includes at least one clickable URL and, where available, a page or section title.
- The answer does not claim that unsupported information came from EDB.
- The agent can answer at least one prepared in-scope question correctly.
- The agent refuses or qualifies an unsupported question using a consistent message.
- The agent handles an ambiguous or edge-case question by asking for clarification or explaining the source limitation.
- The response language follows the user's language where practical.

### FR-006 Out-of-scope and low-evidence handling

**Priority:** Must

The system shall use retrieval evidence, not model confidence alone, to determine whether an answer is supported.

**Acceptance criteria:**

- No-answer behaviour is triggered when retrieval returns no sufficiently relevant source.
- The response identifies the limitation of the watched sources.
- The response may suggest an EDB page only when that page was actually retrieved.
- Prompt injection text found in a source page is treated as untrusted content and is not followed as an instruction.

### FR-007 Agent tool trace

**Priority:** Must

The application shall make agent tool activity reviewable.

**Acceptance criteria:**

- The UI or logs show the tool name, execution status, duration, and result count.
- Sensitive values, API keys, full prompts, and webhook secrets are not exposed.
- At least one successful `search_edb_sources` call can be demonstrated during Q&A.

### FR-008 Manual change check

**Priority:** Must

The application shall provide a visible Refresh or Check for Updates action.

**Acceptance criteria:**

- The action fetches the approved watched pages subject to cache and rate-limit rules.
- Each page is classified as unchanged, changed, newly added, failed, or unavailable.
- The user sees the check time and a page-level summary.
- Repeated clicks while a check is running do not start duplicate concurrent checks.

### FR-009 Content diff

**Priority:** Must

The system shall compare the new normalized content with the last known good snapshot.

**Acceptance criteria:**

- A one-sentence edit to a local test snapshot is detected.
- The output includes the affected page and a readable before-and-after diff or equivalent added and removed text.
- Formatting-only differences are minimized by normalization.
- Unchanged pages do not generate notifications.
- A failed fetch is reported as a fetch failure, not as deletion of the whole page.

### FR-010 Human-readable change summary

**Priority:** Must

The system shall turn a raw diff into a short summary suitable for a parent, teacher, or administrator.

**Acceptance criteria:**

- The summary identifies the page and describes the changed information in plain language.
- Raw HTML is never used as the notification body.
- If LLM summarization fails, a deterministic added-and-removed text summary is still available.
- The summary does not invent the reason for a change.

### FR-011 Webhook notification

**Priority:** Must

The system shall send detected changes to a configurable webhook.

**Acceptance criteria:**

- The webhook URL is supplied through an environment variable and is not committed.
- A notification is sent only when a meaningful change is detected, unless explicit test mode is used.
- The notification includes the page title, URL, change summary, and check time.
- Delivery success or failure is recorded.
- A notification failure does not discard the detected diff or overwrite evidence required for retry.
- A safe test-notification action is available.

### FR-012 Snapshot update policy

**Priority:** Must

The system shall apply a predictable rule for accepting new content as the baseline.

**Acceptance criteria:**

- The initial successful crawl creates a baseline without treating all content as a user-facing change.
- A changed snapshot is not silently accepted before the diff has been saved.
- The implementation documents whether baseline acceptance is automatic after processing or requires confirmation.
- Test mode can restore or recreate a clean baseline.

### FR-013 Demonstration mode

**Priority:** Should

The application should support a deterministic local demonstration that does not require editing the live EDB website.

**Acceptance criteria:**

- A fixture or documented procedure changes one sentence in a local snapshot.
- Running Check for Updates detects the fixture change.
- The same flow produces a readable summary and attempts a webhook notification.
- Demo mode is clearly labelled and cannot be confused with live EDB content.

### FR-014 Optional scheduled check

**Priority:** Could

The project may include a documented daily command or scheduler configuration.

**Acceptance criteria:**

- The same change-checking service is reused by both the UI and the scheduler.
- No second implementation of diff logic is introduced.
- Schedule setup is optional; the manual refresh remains fully functional.

## 6. User interface requirements

The application shall have three clear areas.

### 6.1 Ask EDB

- Question input.
- Submit action.
- Answer with citations.
- Clear unsupported-answer state.
- Expandable tool trace.

### 6.2 Source status

- Number of watched pages.
- Last successful refresh.
- Current cache state.
- Inspectable source allowlist.
- Per-page fetch status where practical.

### 6.3 Updates

- Check for Updates action.
- Current operation state.
- Changed and failed pages.
- Readable diff and summary.
- Notification delivery status.
- Test notification or demo change action if demonstration mode is implemented.

The UI must prioritize clarity and a reliable happy path over visual polish.

## 7. Proposed reference architecture

The final stack may change, but the implementation should preserve these component boundaries:

```text
Web UI
  |-- Ask question ----------------------|
  |                                      v
  |                                 Agent service
  |                                      |
  |                                      v
  |                             search_edb_sources
  |                                      |
  |                                      v
  |                              Local retrieval index
  |
  |-- Check for updates --> Crawl and normalize service
                                  |
                                  v
                           Snapshot and diff service
                                  |
                                  v
                          Summary and webhook service
```

Recommended timebox-friendly implementation:

- Python 3.12 or later.
- Streamlit for the initial UI, or FastAPI plus a small frontend if practising full-stack separation is an explicit goal.
- HTTPX or Requests for fetching.
- Beautiful Soup or selectolax for HTML extraction.
- JSON or SQLite for snapshot metadata.
- A small vector index, hybrid search, or another retrieval method that preserves source metadata.
- Standard-library or equivalent line and block diffing.
- An LLM API that supports tool or function calling.
- Generic webhook delivery with an adapter for the chosen destination.

## 8. Suggested internal data model

### Source document

```text
source_id
canonical_url
page_title
section_title
content
content_hash
fetched_at
http_status
extraction_version
```

### Retrieval chunk

```text
chunk_id
source_id
chunk_text
chunk_index
page_title
section_title
canonical_url
```

### Change record

```text
change_id
source_id
checked_at
old_hash
new_hash
change_type
added_text
removed_text
human_summary
notification_status
```

### Tool trace

```text
trace_id
session_id
tool_name
started_at
duration_ms
status
result_count
safe_error_message
```

## 9. Non-functional requirements

### NFR-001 Explainability

- Core functions must be small enough for the developer to explain during a review.
- Retrieval, grounding, diffing, and notification logic must have clear boundaries.
- Important implementation decisions must be documented.

### NFR-002 Reliability

- Cached content remains usable during a temporary EDB outage.
- Network calls use timeouts and controlled retries.
- A partial crawl failure does not corrupt all snapshots.
- User-visible errors explain what failed and whether cached data is being used.

### NFR-003 Performance

- A cached Q&A response should normally begin within five seconds, excluding exceptional model-provider latency.
- A manual refresh should provide progress or status rather than appearing frozen.
- The retrieval index should be rebuilt only when source content changes.

### NFR-004 Security and privacy

- API keys and webhook URLs are read from environment variables.
- `.env` and local secret files are excluded from version control.
- User questions are not treated as trusted system instructions.
- Retrieved page content is treated as untrusted data.
- The application does not collect personal data beyond transient user questions.
- Logs avoid secrets and unnecessary full question histories.

### NFR-005 Responsible source access

- Content is cached.
- Refreshes are rate-limited.
- Access controls are never bypassed.
- The application is clearly labelled as an unofficial proof of concept and not an EDB service.

### NFR-006 Maintainability

- Configuration, fetching, extraction, retrieval, agent orchestration, diffing, and notification are separate modules or services.
- Business logic is testable without launching the UI.
- External API calls can be replaced with fakes in tests.

### NFR-007 Accessibility and language

- Essential actions can be completed using keyboard input.
- Status is communicated with text rather than colour alone.
- Traditional Chinese content is rendered correctly.
- English interface labels may be used, but source titles and quotations must not be corrupted or silently translated.

## 10. Error handling requirements

The following conditions must have an explicit application response:

- EDB timeout or connection failure.
- Non-200 HTTP response.
- Page extraction produces no meaningful content.
- LLM API key is missing.
- LLM request fails or times out.
- Retrieval returns no relevant passages.
- Webhook URL is missing.
- Webhook delivery is rejected or times out.
- Snapshot file is missing or malformed.
- Multiple refresh attempts occur simultaneously.

The system must distinguish source failure, retrieval failure, model failure, and notification failure rather than returning a single generic error.

## 11. Test requirements

### 11.1 Unit tests

- URL allowlist filtering excludes navigation and off-domain URLs.
- Normalization removes configured boilerplate and collapses irrelevant whitespace.
- Equivalent normalized text produces the same hash.
- A one-sentence change produces a meaningful diff.
- Failed fetches do not overwrite the previous snapshot.
- Citation metadata survives chunking and retrieval.
- Webhook payload excludes raw HTML and secrets.

### 11.2 Integration tests

- Cached source ingestion produces searchable chunks.
- A question invokes the retrieval tool and returns a cited answer.
- A no-evidence question returns the supported refusal response.
- A local snapshot modification creates a change record.
- A detected change generates the expected webhook payload.
- A webhook failure remains visible and retryable.

### 11.3 Required evaluation questions

Before completion, create and document:

1. At least one question clearly answered by the watched pages.
2. At least one question not answered by the watched pages.
3. At least one ambiguous or edge-case question.

Expected evidence, retrieved passages, final response behaviour, and citations must be recorded for each question.

### 11.4 Manual acceptance flow

1. Start the application from a clean checkout using the README.
2. Load or build the source cache.
3. Ask an in-scope question and open its citation.
4. Ask an unsupported question and confirm that the agent does not guess.
5. Inspect the tool trace.
6. Trigger a no-change refresh.
7. Apply the documented local demo change.
8. Trigger another refresh and inspect the diff.
9. Confirm the human-readable summary.
10. Confirm successful notification delivery or an accurately reported delivery failure.

## 12. Observability requirements

- Use structured or consistently formatted logs.
- Assign a request or session identifier to Q&A operations.
- Log fetch duration, HTTP result, extraction result, retrieval result count, tool status, and webhook result.
- Do not log secrets, authorization headers, or complete environment variables.
- Provide enough evidence to explain why a response was answered or refused.

## 13. Configuration requirements

The project should support configuration equivalent to:

```env
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-5.4-mini
OPENROUTER_SITE_URL=http://localhost:3000
OPENROUTER_APP_NAME=EDB Primary Education Agent
NOTIFICATION_WEBHOOK_URL=
SOURCE_SEED_URL=https://www.edb.gov.hk/tc/edu-system/primary-secondary/primary.html
CACHE_TTL_SECONDS=
REQUEST_TIMEOUT_SECONDS=
RETRIEVAL_TOP_K=
RETRIEVAL_MIN_SCORE=0.25
DEMO_MODE=false
```

An `.env.example` file must contain names and safe example values only.

## 14. Deliverables

### 14.1 Repository

- Runnable source code.
- Dependency lock file.
- `.env.example`.
- Tests and fixtures.
- No committed secrets or generated private data.

### 14.2 README

- Project purpose and proof-of-concept disclaimer.
- Architecture summary.
- Prerequisites.
- Installation and start commands.
- Environment variables.
- How to initialize the source cache.
- How to ask the three evaluation question types.
- How to run a live refresh.
- How to trigger the deterministic demo change.
- How to configure and test the webhook.
- How to run tests.
- Known limitations.

### 14.3 Technical note

If prepared, the one-page technical note must state:

- What was built.
- The main architecture and why it was chosen.
- What AI tools drafted or suggested.
- What the developer changed, verified, or rewrote.
- At least one AI suggestion that was rejected and why.
- Known limitations involving cache freshness, rate limits, retrieval quality, evaluations, privacy, and scale.
- What would likely break or require redesign if approximately 20 schools used the system.
- The next engineering step.

### 14.4 Demo

The 3–5 minute demonstration should show:

1. One supported question with a citation.
2. One unsupported or edge-case question.
3. The visible agent tool trace.
4. A no-change refresh.
5. A controlled one-sentence snapshot change.
6. Detection, readable summary, and webhook notification.

## 15. Out of scope for the initial version

- User accounts and authentication.
- School or student data.
- Admin content-management system.
- A full recursive EDB crawler.
- OCR or large-scale PDF ingestion.
- Multiple knowledge domains outside primary education.
- Production-grade multi-tenant infrastructure.
- Guaranteed real-time monitoring.
- Automated legal or policy advice.
- Native mobile applications.
- Complex multi-agent orchestration.

## 16. Timebox plan

| Work item | Target time |
| --- | ---: |
| Project setup and configuration | 0.5 hour |
| Source discovery, extraction, and cache | 2 hours |
| Retrieval and agent tool calling | 2 hours |
| Grounded answers, citations, and refusal handling | 1.5 hours |
| Change detection, summary, and webhook | 2 hours |
| UI integration and error states | 1.5 hours |
| Tests, README, technical note outline, and demo preparation | 2 hours |
| Contingency | 0.5 hour |

Total target: 12 hours.

If time is limited, reduce visual polish and optional scheduling before reducing grounding, diff correctness, notification evidence, or documentation.

## 17. Definition of done

The initial version is complete only when all of the following are true:

- A reviewer can start the application from the README.
- The watched source list is explicit and limited.
- The agent invokes a real retrieval tool.
- A supported answer includes a verifiable citation.
- An unsupported answer does not hallucinate.
- Tool activity is visible without exposing secrets.
- Manual refresh works and is rate-limited.
- A controlled one-sentence change is detected.
- The resulting change description is understandable without reading HTML.
- A webhook notification succeeds or reports failure accurately.
- Core tests pass.
- Known limitations and AI-assisted development are documented honestly.

## 18. Open implementation decisions

These choices should be made before implementation begins:

1. **Practice depth:** timebox-faithful Streamlit proof of concept, or FastAPI plus a separate frontend for deeper full-stack practice.
2. **LLM provider:** provider and model used for tool calling and summarization.
3. **Retrieval method:** lightweight local embeddings, hybrid retrieval, or another explainable method.
4. **Persistence:** JSON files for simplicity or SQLite for stronger history and query support.
5. **Webhook destination:** generic test endpoint, Discord, Slack, Telegram, or another approved endpoint.
6. **Baseline acceptance:** automatic after a saved diff and notification attempt, or explicit user confirmation.
7. **Language:** Traditional Chinese-first responses or automatic response-language matching.
