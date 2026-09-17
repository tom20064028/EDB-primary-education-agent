from __future__ import annotations

import httpx

from .models import NotificationResult


class WebhookNotifier:
    def __init__(
        self,
        webhook_url: str | None,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def send(self, *, title: str, message: str, url: str | None = None) -> NotificationResult:
        if not self.webhook_url:
            return NotificationResult(status="skipped", detail="Webhook URL is not configured")

        payload = {
            "text": f"{title}\n{message}" + (f"\n{url}" if url else ""),
            "title": title,
            "message": message,
            "url": url,
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds, transport=self.transport
            ) as client:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
        except httpx.TimeoutException:
            return NotificationResult(status="failed", detail="Webhook request timed out")
        except httpx.HTTPStatusError as exc:
            return NotificationResult(
                status="failed", detail=f"Webhook returned HTTP {exc.response.status_code}"
            )
        except httpx.HTTPError as exc:
            return NotificationResult(status="failed", detail=f"Webhook request failed: {exc}")
        return NotificationResult(
            status="sent", detail=f"Webhook accepted with HTTP {response.status_code}"
        )
