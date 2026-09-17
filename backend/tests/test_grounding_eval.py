from datetime import UTC, datetime

from edb_agent.extractor import build_chunks, extract_document
from edb_agent.retrieval import RetrievalService
from edb_agent.storage import Storage


def test_unrelated_question_does_not_pass_evidence_threshold(tmp_path) -> None:
    storage = Storage(tmp_path / "eval.sqlite3")
    storage.initialize()
    url = "https://www.edb.gov.hk/tc/edu-system/primary-secondary/primary/index.html"
    document = extract_document(
        """
        <html><h1>小學教育</h1><div class="generic_page_content">
        <h2>支援服務</h2><p>教育局提供校本支援服務及學習安排。</p>
        <h2>辦學模式</h2><p>一條龍辦學模式連繫中小學教育。</p>
        </div></html>
        """,
        url,
    )
    now = datetime.now(UTC).isoformat()
    storage.upsert_allowlist([(url, document.title, True)], now)
    storage.replace_source(document, now, build_chunks(document))
    retrieval = RetrievalService(storage)

    assert retrieval.search("甚麼是一條龍辦學模式？", min_score=0.25)
    assert retrieval.search("教育局有沒有提供校服折扣？", min_score=0.25) == []
