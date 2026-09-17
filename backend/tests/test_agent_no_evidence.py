import json
from types import SimpleNamespace

from edb_agent.agent import INSUFFICIENT_EVIDENCE_ANSWER, AgentService
from edb_agent.retrieval import RetrievalService
from edb_agent.storage import Storage


class FakeResponses:
    def __init__(self) -> None:
        self.calls = 0

    async def create(self, **_kwargs):
        self.calls += 1
        if self.calls > 1:
            raise AssertionError("The model must not receive a second request without evidence")
        tool_call = SimpleNamespace(
            type="function_call",
            name="search_edb_sources",
            arguments=json.dumps({"query": "火星上的小學如何收生？", "max_results": 5}),
            call_id="call-test",
        )
        return SimpleNamespace(output=[tool_call], output_text="")


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


async def test_llm_path_stops_after_zero_search_results(tmp_path) -> None:
    storage = Storage(tmp_path / "agent.sqlite3")
    storage.initialize()
    service = AgentService(
        storage,
        RetrievalService(storage),
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        default_headers={},
        model="openai/gpt-5.4-mini",
        top_k=5,
        min_score=0.25,
    )
    fake_client = FakeClient()
    service.client = fake_client

    response = await service.answer("火星上的小學如何收生？")

    assert fake_client.responses.calls == 1
    assert response.answer == INSUFFICIENT_EVIDENCE_ANSWER
    assert response.supported is False
    assert response.citations == []
    assert response.mode == "llm-agent"
    assert response.traces[0].result_count == 0
