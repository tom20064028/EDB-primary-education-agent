from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from .crawler import EDBCrawler, FetchFailure
from .diffing import content_diff, human_summary
from .extractor import build_chunks
from .models import (
    ChangeRecord,
    DemoMutationResponse,
    PageRefreshResult,
    RefreshResponse,
)
from .notifier import WebhookNotifier
from .storage import Storage

DEMO_MARKER = "【示範變更】此句只存在於本地快照，用作測試變更偵測。"


class SourceService:
    def __init__(self, storage: Storage, crawler: EDBCrawler, notifier: WebhookNotifier):
        self.storage = storage
        self.crawler = crawler
        self.notifier = notifier

    async def bootstrap(self, seed_url: str) -> RefreshResponse:
        checked_at = datetime.now(UTC).isoformat()
        seed = await self.crawler.fetch(seed_url, discover_links=True)
        entries = [(seed.url, seed.title, True)] + [
            (link["url"], link["title"], False) for link in seed.discovered_links
        ]
        self.storage.upsert_allowlist(entries, checked_at)

        results: list[PageRefreshResult] = []
        documents = {seed.url: seed}
        for entry_url, entry_title, _is_seed in entries:
            try:
                document = documents.get(entry_url) or await self.crawler.fetch(entry_url)
                self.storage.replace_source(document, checked_at, build_chunks(document))
                results.append(
                    PageRefreshResult(
                        url=document.url,
                        title=document.title,
                        status="new",
                        detail="Baseline saved",
                    )
                )
            except FetchFailure as exc:
                self.storage.mark_source_error(entry_url, entry_title, checked_at, str(exc))
                results.append(
                    PageRefreshResult(
                        url=entry_url, title=entry_title, status="failed", detail=str(exc)
                    )
                )
            await self.crawler.polite_pause()
        return RefreshResponse(checked_at=checked_at, results=results, changes=[])

    async def refresh(self, *, notify: bool) -> RefreshResponse:
        checked_at = datetime.now(UTC).isoformat()
        allowlist = self.storage.list_allowlist()
        results: list[PageRefreshResult] = []
        changes: list[ChangeRecord] = []

        for entry in allowlist:
            url = str(entry["url"])
            title = str(entry["title"])
            previous = self.storage.get_source(url)
            try:
                document = await self.crawler.fetch(url, discover_links=bool(entry["is_seed"]))
            except FetchFailure as exc:
                self.storage.mark_source_error(url, title, checked_at, str(exc))
                results.append(
                    PageRefreshResult(url=url, title=title, status="failed", detail=str(exc))
                )
                await self.crawler.polite_pause()
                continue

            if previous is None or not previous["content_hash"]:
                self.storage.replace_source(document, checked_at, build_chunks(document))
                results.append(
                    PageRefreshResult(
                        url=document.url,
                        title=document.title,
                        status="new",
                        detail="New baseline saved",
                    )
                )
            elif previous["content_hash"] == document.content_hash:
                self.storage.replace_source(document, checked_at, build_chunks(document))
                results.append(
                    PageRefreshResult(
                        url=document.url,
                        title=document.title,
                        status="unchanged",
                        detail="No meaningful text change",
                    )
                )
            else:
                added, removed = content_diff(
                    previous["normalized_content"], document.normalized_content
                )
                summary = human_summary(document.title, added, removed)
                notification = (
                    await self.notifier.send(
                        title="EDB page updated", message=summary, url=document.url
                    )
                    if notify
                    else None
                )
                change = ChangeRecord(
                    change_id=str(uuid4()),
                    url=document.url,
                    page_title=document.title,
                    checked_at=checked_at,
                    old_hash=previous["content_hash"],
                    new_hash=document.content_hash,
                    added_text=added[:20],
                    removed_text=removed[:20],
                    human_summary=summary,
                    notification_status=notification.status if notification else "skipped",
                    notification_error=(
                        notification.detail
                        if notification and notification.status == "failed"
                        else None
                    ),
                )
                self.storage.insert_change(change)
                self.storage.replace_source(document, checked_at, build_chunks(document))
                changes.append(change)
                results.append(
                    PageRefreshResult(
                        url=document.url,
                        title=document.title,
                        status="changed",
                        detail=summary,
                        change_id=change.change_id,
                    )
                )
            await self.crawler.polite_pause()

        return RefreshResponse(checked_at=checked_at, results=results, changes=changes)

    def inject_demo_change(self) -> DemoMutationResponse:
        result = self.storage.mutate_source_for_demo(DEMO_MARKER)
        if result is None:
            raise RuntimeError("Initialize the EDB source cache before using demo mode")
        url, title = result
        return DemoMutationResponse(
            url=url,
            title=title,
            detail=(
                "A clearly labelled sentence was added to the local snapshot. "
                "The next live refresh should detect its removal."
            ),
        )
