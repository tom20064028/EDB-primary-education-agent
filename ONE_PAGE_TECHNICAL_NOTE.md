# EDB Primary Education Agent Technical Note

## What I built

I built an unofficial web application that answers questions from a controlled set of public Hong Kong Education Bureau primary-education pages. A Next.js dashboard calls a FastAPI service, which caches normalized page content in SQLite and exposes a `search_edb_sources` tool. The agent uses OpenRouter through the OpenAI Python SDK, but answers only from passages returned by local retrieval. Every supported answer includes source metadata and a visible tool trace. If retrieval finds no sufficient evidence, the backend returns a deterministic no-answer response without making a second model request.

The same application monitors its allowlisted pages. An initial crawl creates the baseline. A manual refresh fetches the pages, normalizes the text, compares content hashes, stores readable added-and-removed text, and optionally sends a plain-language webhook notification. A labelled local mutation provides a repeatable demonstration without changing the EDB website.

## What the model drafted and what I changed

I used an AI coding assistant to draft the initial requirements, repository structure, backend modules, tests, dashboard components, and documentation. I chose the separated FastAPI and Next.js architecture and later changed the provider integration to OpenRouter. Testing then exposed several weaknesses in the first draft. I replaced Chinese character unigrams with bigrams and trigrams, raised the evidence threshold, added unsupported-question tests, fixed the local CORS configuration, and made no-evidence behaviour deterministic. I also stopped the model from broadening a user question when it calls the search tool; `AgentService.answer` executes retrieval against the original question, because tool arguments are model output rather than trusted evidence.

## One suggestion I rejected

I rejected a broad recursive crawler. The assessment asks for the primary-education page and pages it clearly links, so the crawler keeps only the seed page and direct links from its main content area. Recursive discovery would increase irrelevant retrieval results, place more load on the government site, and make the evidence boundary harder to explain.

## What I would do next

I would first build a larger labelled evaluation set and measure retrieval precision, refusal accuracy, and citation correctness before introducing hybrid keyword and embedding retrieval. For use by 20 schools, the current single-process SQLite store and synchronous refresh loop would also need a shared database, queued scheduled jobs, webhook retries, authentication, tenant separation, rate controls, secrets management, and monitoring. The application uses public information only and is a proof of concept, not a production service.
