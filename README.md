# EDB Primary Education Agent

An unofficial practice project that answers questions from a controlled set of public Hong Kong Education Bureau pages and detects meaningful changes to those pages.

The system demonstrates:

- Grounded Q&A with source citations.
- An explicit `search_edb_sources` agent tool and visible trace.
- Conservative first-level EDB source discovery and local caching.
- Normalized snapshots, content hashes, readable diffs, and webhook delivery.
- Deterministic retrieval-only behaviour when no LLM key is configured.

This proof of concept is not affiliated with the Education Bureau and is not production-ready.

## Architecture

```text
Next.js dashboard (port 3000)
        |
        v
FastAPI service (port 8000)
        |-- crawler + HTML normalization
        |-- SQLite source cache and change history
        |-- local Chinese/English hybrid retrieval
        |-- OpenRouter Responses API function calling (optional)
        `-- generic webhook notification (optional)
```

## Prerequisites

- Python 3.12 or later.
- Node.js 20 or later.
- pnpm 11.
- Internet access for the initial EDB crawl.
- Optional: an OpenRouter API key and a generic webhook URL.

## 1. Configure environment variables

```bash
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
```

The application works in retrieval-only mode without `OPENROUTER_API_KEY`. In that mode it returns the most relevant source excerpts instead of a generated answer.

Important variables:

- `OPENROUTER_API_KEY`: enables OpenRouter Responses API function calling.
- `OPENROUTER_BASE_URL`: defaults to `https://openrouter.ai/api/v1`.
- `OPENROUTER_MODEL`: defaults to `openai/gpt-5.4-mini`; choose an OpenRouter model that supports tool calling.
- `OPENROUTER_SITE_URL` and `OPENROUTER_APP_NAME`: identify the local app through OpenRouter's optional attribution headers.
- `NOTIFICATION_WEBHOOK_URL`: receives JSON containing `title`, `message`, `url`, and a generic `text` field.
- `RETRIEVAL_MIN_SCORE`: evidence threshold used before an answer is treated as supported.
- `NEXT_PUBLIC_API_BASE_URL`: FastAPI origin used by the browser.

Never commit `.env` or `frontend/.env.local`.

## 2. Install the backend

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e 'backend[dev]'
```

## 3. Install the frontend

```bash
cd frontend
pnpm install
cd ..
```

## 4. Start both services

Terminal one:

```bash
.venv/bin/uvicorn edb_agent.main:app --reload --port 8000
```

Terminal two:

```bash
cd frontend
pnpm dev
```

Open http://localhost:3000. FastAPI documentation is available at http://localhost:8000/docs.

## 5. Initialize the source cache

Click **Initialize sources** in the dashboard. The backend will:

1. Fetch the configured EDB primary-education seed page.
2. Extract only links in its primary content area.
3. Persist the seed page and 11 approved direct pages.
4. Normalize the pages into local retrieval chunks.

The first successful crawl creates a baseline and does not produce user-facing change alerts.

## Main demonstration path

### Grounded question

Ask:

> 甚麼是「一條龍」辦學模式？

Expected result: source evidence is found, citations link to allowlisted EDB pages, and the trace shows `search_edb_sources`.

### Unsupported question

Ask:

> 教育局有沒有提供校服折扣？

Expected result: the watched sources are reported as insufficient. The app does not guess.

### Edge case

Ask:

> 火星上的小學如何收生？

Expected result: no answer is asserted from unrelated Hong Kong school-admission content.

## Change-detection demonstration

1. Click **Inject demo change**. This adds a clearly labelled sentence to one local snapshot only.
2. Click **Check for updates**.
3. The live EDB copy no longer contains that sentence, so the app records a one-line removal.
4. Inspect the readable Chinese summary and the expandable text diff.
5. If a webhook is configured, inspect the delivery status.

The demo mutation is local and never writes to the EDB website.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Configuration and service status |
| `GET` | `/api/sources` | Allowlisted source and cache status |
| `POST` | `/api/sources/bootstrap` | Discover direct links and create the baseline |
| `POST` | `/api/sources/refresh` | Fetch, normalize, diff, and optionally notify |
| `POST` | `/api/chat` | Run grounded retrieval and optional LLM tool calling |
| `GET` | `/api/changes` | Read recorded meaningful changes |
| `POST` | `/api/demo/mutate-snapshot` | Apply a controlled local demo mutation |
| `POST` | `/api/notifications/test` | Send a safe test payload |

## Verification

Backend:

```bash
.venv/bin/ruff check backend
.venv/bin/pytest -q -c backend/pyproject.toml backend/tests
```

Frontend:

```bash
cd frontend
pnpm lint
pnpm build
```

## Current limitations

- The local retrieval algorithm is deliberately lightweight; it is not a full semantic embedding pipeline.
- The evidence threshold is conservative and may refuse broad but answerable questions.
- HTML extraction is tailored to current EDB content containers and needs monitoring if the site is redesigned.
- Snapshot history is local SQLite and is not suitable for multiple application instances.
- Webhook delivery has no background retry queue.
- The application has no authentication, audit retention policy, or multi-school tenancy.
- A class or school-scale deployment would require a shared database, job queue, scheduler, rate controls, evaluation dataset, secrets management, and operational monitoring.

## AI-assisted development

AI coding assistance was used to draft requirements, implementation, tests, and interface copy. See [AI_DEVELOPMENT_LOG.md](AI_DEVELOPMENT_LOG.md) for the working record. Anyone presenting or submitting this project should review the code, run the acceptance flow, document their own changes, and be able to explain every core function.
