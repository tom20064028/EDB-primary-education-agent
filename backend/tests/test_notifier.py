import httpx

from edb_agent.notifier import WebhookNotifier


async def test_webhook_payload_contains_plain_text() -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.update(__import__("json").loads(request.content))
        return httpx.Response(204)

    notifier = WebhookNotifier(
        "https://hooks.example.test/edb",
        2,
        transport=httpx.MockTransport(handler),
    )
    result = await notifier.send(
        title="EDB page updated",
        message="A sentence changed.",
        url="https://www.edb.gov.hk/tc/page.html",
    )

    assert result.status == "sent"
    assert captured["message"] == "A sentence changed."
    assert "<html" not in str(captured)


async def test_missing_webhook_is_reported_as_skipped() -> None:
    result = await WebhookNotifier(None, 2).send(title="Test", message="Hello")
    assert result.status == "skipped"
