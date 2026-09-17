from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .models import ChangeRecord, ExtractedDocument, SourceSummary, ToolTrace

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS allowlist (
    url TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    is_seed INTEGER NOT NULL DEFAULT 0,
    discovered_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    url TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    normalized_content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    status TEXT NOT NULL,
    error TEXT,
    FOREIGN KEY(url) REFERENCES allowlist(url) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    page_title TEXT NOT NULL,
    section_title TEXT NOT NULL,
    text TEXT NOT NULL,
    position INTEGER NOT NULL,
    FOREIGN KEY(url) REFERENCES sources(url) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chunks_url ON chunks(url);

CREATE TABLE IF NOT EXISTS changes (
    change_id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    page_title TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    old_hash TEXT NOT NULL,
    new_hash TEXT NOT NULL,
    added_text TEXT NOT NULL,
    removed_text TEXT NOT NULL,
    human_summary TEXT NOT NULL,
    notification_status TEXT NOT NULL,
    notification_error TEXT
);

CREATE INDEX IF NOT EXISTS idx_changes_checked_at ON changes(checked_at DESC);

CREATE TABLE IF NOT EXISTS tool_traces (
    trace_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    started_at TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    status TEXT NOT NULL,
    result_count INTEGER NOT NULL,
    safe_error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_tool_traces_session ON tool_traces(session_id);
"""


class Storage:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.Lock()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def initialize(self) -> None:
        with self._write_lock, self._connect() as connection:
            connection.executescript(SCHEMA)

    def upsert_allowlist(
        self, entries: Iterable[tuple[str, str, bool]], discovered_at: str
    ) -> None:
        rows = [(url, title, int(is_seed), discovered_at) for url, title, is_seed in entries]
        with self._write_lock, self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO allowlist(url, title, is_seed, discovered_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title=excluded.title,
                    is_seed=excluded.is_seed,
                    discovered_at=excluded.discovered_at
                """,
                rows,
            )

    def list_allowlist(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT url, title, is_seed, discovered_at
                FROM allowlist
                ORDER BY is_seed DESC, title
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_source(self, url: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM sources WHERE url = ?", (url,)).fetchone()
        return dict(row) if row else None

    def list_sources(self) -> list[SourceSummary]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    a.url,
                    a.title,
                    a.is_seed,
                    s.content_hash,
                    s.fetched_at,
                    COALESCE(s.status, 'pending') AS status,
                    s.error,
                    COUNT(c.chunk_id) AS chunk_count
                FROM allowlist a
                LEFT JOIN sources s ON s.url = a.url
                LEFT JOIN chunks c ON c.url = a.url
                GROUP BY a.url, a.title, a.is_seed, s.content_hash, s.fetched_at, s.status, s.error
                ORDER BY a.is_seed DESC, a.title
                """
            ).fetchall()
        summaries: list[SourceSummary] = []
        for row in rows:
            data = dict(row)
            data["is_seed"] = bool(data["is_seed"])
            summaries.append(SourceSummary(**data))
        return summaries

    def replace_source(
        self,
        document: ExtractedDocument,
        fetched_at: str,
        chunks: Iterable[dict[str, Any]],
    ) -> None:
        with self._write_lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sources(
                    url, title, normalized_content, content_hash, fetched_at, status, error
                )
                VALUES (?, ?, ?, ?, ?, 'ready', NULL)
                ON CONFLICT(url) DO UPDATE SET
                    title=excluded.title,
                    normalized_content=excluded.normalized_content,
                    content_hash=excluded.content_hash,
                    fetched_at=excluded.fetched_at,
                    status='ready',
                    error=NULL
                """,
                (
                    document.url,
                    document.title,
                    document.normalized_content,
                    document.content_hash,
                    fetched_at,
                ),
            )
            connection.execute("DELETE FROM chunks WHERE url = ?", (document.url,))
            connection.executemany(
                """
                INSERT INTO chunks(chunk_id, url, page_title, section_title, text, position)
                VALUES (:chunk_id, :url, :page_title, :section_title, :text, :position)
                """,
                list(chunks),
            )

    def mark_source_error(self, url: str, title: str, fetched_at: str, error: str) -> None:
        existing = self.get_source(url)
        if existing:
            with self._write_lock, self._connect() as connection:
                connection.execute(
                    "UPDATE sources SET status='stale', error=?, fetched_at=? WHERE url=?",
                    (error, fetched_at, url),
                )
            return

        with self._write_lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sources(
                    url, title, normalized_content, content_hash, fetched_at, status, error
                )
                VALUES (?, ?, '', '', ?, 'failed', ?)
                """,
                (url, title, fetched_at, error),
            )

    def all_chunks(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT chunk_id, url, page_title, section_title, text FROM chunks"
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_change(self, change: ChangeRecord) -> None:
        with self._write_lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO changes(
                    change_id, url, page_title, checked_at, old_hash, new_hash,
                    added_text, removed_text, human_summary,
                    notification_status, notification_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change.change_id,
                    change.url,
                    change.page_title,
                    change.checked_at,
                    change.old_hash,
                    change.new_hash,
                    json.dumps(change.added_text, ensure_ascii=False),
                    json.dumps(change.removed_text, ensure_ascii=False),
                    change.human_summary,
                    change.notification_status,
                    change.notification_error,
                ),
            )

    def list_changes(self, limit: int = 20) -> list[ChangeRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM changes ORDER BY checked_at DESC LIMIT ?", (limit,)
            ).fetchall()
        changes: list[ChangeRecord] = []
        for row in rows:
            data = dict(row)
            data["added_text"] = json.loads(data["added_text"])
            data["removed_text"] = json.loads(data["removed_text"])
            changes.append(ChangeRecord(**data))
        return changes

    def insert_trace(self, session_id: str, started_at: str, trace: ToolTrace) -> None:
        with self._write_lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tool_traces(
                    trace_id, session_id, tool_name, started_at, duration_ms,
                    status, result_count, safe_error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace.trace_id,
                    session_id,
                    trace.tool_name,
                    started_at,
                    trace.duration_ms,
                    trace.status,
                    trace.result_count,
                    trace.safe_error_message,
                ),
            )

    def mutate_source_for_demo(self, marker: str) -> tuple[str, str] | None:
        with self._write_lock, self._connect() as connection:
            row = connection.execute(
                """
                SELECT s.url, s.title, s.normalized_content
                FROM sources s JOIN allowlist a ON a.url = s.url
                WHERE s.status IN ('ready', 'stale')
                ORDER BY a.is_seed DESC, s.title
                LIMIT 1
                """
            ).fetchone()
            if not row:
                return None
            content = row["normalized_content"]
            if marker not in content:
                content = f"{content}\n{marker}"
            import hashlib

            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            connection.execute(
                "UPDATE sources SET normalized_content=?, content_hash=? WHERE url=?",
                (content, content_hash, row["url"]),
            )
        return str(row["url"]), str(row["title"])
