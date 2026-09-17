from datetime import UTC, datetime

from edb_agent.extractor import build_chunks, extract_document
from edb_agent.retrieval import RetrievalService
from edb_agent.storage import Storage


def test_chinese_retrieval_preserves_citation_metadata(tmp_path) -> None:
    storage = Storage(tmp_path / "test.sqlite3")
    storage.initialize()
    url = "https://www.edb.gov.hk/tc/edu-system/primary-secondary/primary/index.html"
    document = extract_document(
        """
        <html><h1>概覽及工作重點</h1><div class="generic_page_content">
        <h2>免費教育</h2><p>政府透過公營學校提供十二年免費中小學教育。</p>
        <h2>學習安排</h2><p>學校按課程指引安排學習活動。</p>
        </div></html>
        """,
        url,
    )
    now = datetime.now(UTC).isoformat()
    storage.upsert_allowlist([(url, document.title, True)], now)
    storage.replace_source(document, now, build_chunks(document))

    results = RetrievalService(storage).search("免費教育有多少年？", top_k=3, min_score=0)

    assert results
    assert results[0].url == url
    assert results[0].page_title == "概覽及工作重點"
    assert "免費" in results[0].text


def test_empty_index_returns_no_result(tmp_path) -> None:
    storage = Storage(tmp_path / "empty.sqlite3")
    storage.initialize()
    assert RetrievalService(storage).search("小學教育") == []
