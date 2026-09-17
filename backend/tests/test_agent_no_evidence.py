import json
from datetime import UTC, datetime
from types import SimpleNamespace

from edb_agent.agent import INSUFFICIENT_EVIDENCE_ANSWER, AgentService
from edb_agent.extractor import build_chunks, extract_document
from edb_agent.retrieval import RetrievalService
from edb_agent.storage import Storage


class FakeResponses:
    def __init__(self, tool_query: str) -> None:
        self.calls = 0
        self.tool_query = tool_query

    async def create(self, **_kwargs):
        self.calls += 1
        if self.calls > 1:
            raise AssertionError("The model must not receive a second request without evidence")
        tool_call = SimpleNamespace(
            type="function_call",
            name="search_edb_sources",
            arguments=json.dumps({"query": self.tool_query, "max_results": 5}),
            call_id="call-test",
        )
        return SimpleNamespace(output=[tool_call], output_text="")


class FakeClient:
    def __init__(self, tool_query: str) -> None:
        self.responses = FakeResponses(tool_query)


def build_service(storage: Storage) -> AgentService:
    return AgentService(
        storage,
        RetrievalService(storage),
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        default_headers={},
        model="openai/gpt-5.4-mini",
        top_k=5,
        min_score=0.25,
    )


async def test_llm_path_stops_after_zero_search_results(tmp_path) -> None:
    storage = Storage(tmp_path / "agent.sqlite3")
    storage.initialize()
    service = build_service(storage)
    fake_client = FakeClient("火星上的小學如何收生？")
    service.client = fake_client

    response = await service.answer("火星上的小學如何收生？")

    assert fake_client.responses.calls == 1
    assert response.answer == INSUFFICIENT_EVIDENCE_ANSWER
    assert response.supported is False
    assert response.citations == []
    assert response.mode == "llm-agent"
    assert response.traces[0].result_count == 0


async def test_model_cannot_broaden_query_into_irrelevant_evidence(tmp_path) -> None:
    storage = Storage(tmp_path / "agent.sqlite3")
    storage.initialize()
    url = "https://www.edb.gov.hk/tc/edu-system/primary-secondary/primary/index.html"
    document = extract_document(
        """
        <html><h1>小學教育</h1><div class="generic_page_content">
        <h2>支援服務</h2><p>教育局提供校本支援服務及學習安排。</p>
        <h2>數字教育</h2><p>教育局推動小學數字教育。</p>
        </div></html>
        """,
        url,
    )
    now = datetime.now(UTC).isoformat()
    storage.upsert_allowlist([(url, document.title, True)], now)
    storage.replace_source(document, now, build_chunks(document))

    service = build_service(storage)
    fake_client = FakeClient("教育局")
    service.client = fake_client

    response = await service.answer("教育局有沒有提供校服折扣？")

    assert fake_client.responses.calls == 1
    assert response.answer == INSUFFICIENT_EVIDENCE_ANSWER
    assert response.supported is False
    assert response.citations == []
    assert response.traces[0].result_count == 0
