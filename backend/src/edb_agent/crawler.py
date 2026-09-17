from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from .extractor import canonicalize_url, extract_document
from .models import ExtractedDocument

USER_AGENT = "EDBPrimaryEducationPracticeAgent/0.1 (educational proof of concept)"


@dataclass(slots=True)
class FetchFailure(Exception):
    url: str
    message: str

    def __str__(self) -> str:
        return self.message


class EDBCrawler:
    def __init__(self, timeout_seconds: float, transport: httpx.AsyncBaseTransport | None = None):
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def fetch(self, url: str, *, discover_links: bool = False) -> ExtractedDocument:
        canonical = canonicalize_url(url, url)
        if canonical is None:
            raise FetchFailure(url, "URL is outside the approved EDB host allowlist")

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                follow_redirects=True,
                headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
                transport=self.transport,
            ) as client:
                response = await client.get(canonical)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise FetchFailure(canonical, "EDB request timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise FetchFailure(canonical, f"EDB returned HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise FetchFailure(canonical, f"Could not fetch EDB page: {exc}") from exc

        final_url = canonicalize_url(canonical, str(response.url))
        if final_url is None:
            raise FetchFailure(canonical, "EDB redirected to an unapproved host")
        try:
            return extract_document(response.text, final_url, discover_links=discover_links)
        except ValueError as exc:
            raise FetchFailure(final_url, str(exc)) from exc

    async def polite_pause(self) -> None:
        await asyncio.sleep(0.2)
