# AI Assisted Development Log

## Purpose

This file records AI involvement and human decisions during the practice project. It is a working log, not a claim that the current repository was independently authored by the developer.

## Initial scope decisions

- Human decision: selected Task 1 rather than Task 2.
- Human decision: treated the exercise as practice first, with possible later submission.
- Human decision: selected a separated FastAPI and Next.js architecture for deeper full-stack practice instead of the fastest Streamlit option.

## AI drafted or materially assisted

- Initial technical requirements and acceptance criteria.
- FastAPI and Next.js repository structure.
- EDB HTML extraction, SQLite storage, retrieval, diff, webhook, and API modules.
- OpenRouter Responses API function-calling integration through the OpenAI Python SDK.
- Initial unit tests and evaluation questions.
- Dashboard components, styling, README, and this development log.

## Review and changes made during implementation

### Source discovery check

The implementation was tested against the live public seed page. It extracted the seed plus 11 direct primary-content links and excluded global navigation links.

### Retrieval rejection issue

The initial AI-drafted retriever used Chinese character unigrams and an evidence threshold of `0.04`. A live-cache evaluation showed that an unsupported question about school-uniform discounts still retrieved unrelated passages because common characters such as `校` matched many pages.

The implementation was changed to:

- Use Chinese bigrams and trigrams instead of general single-character tokens.
- Retain a single-character fallback only for one-character queries.
- Raise the default evidence threshold to `0.25`.
- Add a regression test covering the unsupported discount question.

After the change:

- `甚麼是「一條龍」辦學模式？` returns evidence.
- `教育局有沒有提供校服折扣？` is rejected as unsupported.
- `火星上的小學如何收生？` is rejected as unsupported.

### Change-detection check

A clearly labelled sentence was inserted into a local snapshot. The next live refresh detected exactly one changed page, recorded the removed sentence, and produced a readable summary. No notification was sent during this test.

### Browser integration check

The first end-to-end browser run exposed a CORS mismatch: the API allowed
`http://localhost:3000`, while the local browser used `http://127.0.0.1:3000`.
The default allowlist and example environment file were updated to include both
explicit local origins, and a regression test was added. The repeated browser run
then completed supported Q&A, unsupported-question rejection, source display,
demo mutation, and live refresh successfully.

### LLM provider change

The initial AI draft targeted the OpenAI API directly. The implementation was
subsequently changed to OpenRouter at the human developer's request. It now uses
an explicit OpenRouter API key, base URL, provider-qualified model slug, and the
optional application attribution headers while retaining the Responses API tool loop.

### Deterministic no-evidence behaviour

Live OpenRouter testing showed that a model could correctly report zero evidence but
then offer to broaden the search or continue with a hypothetical topic. The application
now stops before the final model call whenever local retrieval returns zero results and
returns one deterministic refusal sentence. A regression test verifies that a zero-result
tool call causes exactly one provider request. The browser error parser was also hardened
so FastAPI validation arrays cannot render as `[object Object]`.

## AI suggestions rejected or constrained

- A broad recursive EDB crawler was rejected. The implementation is limited to links in the seed page's primary content area because recursive crawling increases noise, load, and scope ambiguity.
- Embedding infrastructure was deferred. A local explainable retriever is sufficient for the first practice version and makes no-answer behaviour easier to inspect.
- Automatic scheduling was deferred. A manual refresh exercises the same core workflow with less operational setup.
- Raw model confidence is not accepted as evidence. Support is determined from retrieved source results and a configured threshold.

## Human review still required before any submission

- Read and explain the crawler, normalization, retrieval scoring, tool-call loop, diff logic, and snapshot update policy.
- Configure and test a real LLM key.
- Configure and test a real webhook destination.
- Review the three evaluation questions and add more boundary cases.
- Record any human-authored changes and why they were made.
- Confirm that the one-page technical note accurately distinguishes AI drafts from human work.
