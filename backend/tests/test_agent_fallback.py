from datetime import UTC, datetime

from edb_agent.agent import AgentService
from edb_agent.extractor import build_chunks, extract_document
from edb_agent.retrieval import RetrievalService
from edb_agent.storage import Storage


async def test_retrieval_only_mode_is_cited_and_traced(tmp_path) -> None:
    storage = Storage(tmp_path / "agent.sqlite3")
    storage.initialize()
    url = "https://www.edb.gov.hk/tc/edu-system/primary-secondary/primary/index.html"
    document = extract_document(
        "<html><h1>小學教育</h1><div class='generic_page_content'>"
        "<h2>學習</h2><p>小學教育設有不同學習安排。</p></div></html>",
        url,
    )
    now = datetime.now(UTC).isoformat()
    storage.upsert_allowlist([(url, document.title, True)], now)
    storage.replace_source(document, now, build_chunks(document))
    service = AgentService(
        storage,
        RetrievalService(storage),
        api_key=None,
        base_url="https://openrouter.ai/api/v1",
        default_headers={},
        model="unused",
        top_k=3,
        min_score=0,
    )

    response = await service.answer("有甚麼學習安排？")

    assert response.mode == "retrieval-only"
    assert response.supported is True
    assert response.citations[0].url == url
    assert response.traces[0].tool_name == "search_edb_sources"
    assert response.traces[0].status == "success"
