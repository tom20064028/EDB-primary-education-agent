from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ExtractedSection(BaseModel):
    heading: str
    text: str


class ExtractedDocument(BaseModel):
    url: str
    title: str
    normalized_content: str
    content_hash: str
    sections: list[ExtractedSection]
    discovered_links: list[dict[str, str]] = Field(default_factory=list)


class SourceSummary(BaseModel):
    url: str
    title: str
    content_hash: str | None = None
    fetched_at: str | None = None
    status: str
    error: str | None = None
    is_seed: bool = False
    chunk_count: int = 0


class SearchResult(BaseModel):
    chunk_id: str
    url: str
    page_title: str
    section_title: str
    text: str
    score: float


class Citation(BaseModel):
    title: str
    section: str
    url: str


class ToolTrace(BaseModel):
    trace_id: str
    tool_name: str
    status: Literal["success", "error"]
    duration_ms: int
    result_count: int
    safe_error_message: str | None = None


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    traces: list[ToolTrace]
    mode: Literal["llm-agent", "retrieval-only"]
    supported: bool


class RefreshRequest(BaseModel):
    notify: bool = True


class PageRefreshResult(BaseModel):
    url: str
    title: str
    status: Literal["unchanged", "changed", "new", "failed"]
    detail: str | None = None
    change_id: str | None = None


class ChangeRecord(BaseModel):
    change_id: str
    url: str
    page_title: str
    checked_at: str
    old_hash: str
    new_hash: str
    added_text: list[str]
    removed_text: list[str]
    human_summary: str
    notification_status: str
    notification_error: str | None = None


class RefreshResponse(BaseModel):
    checked_at: str
    results: list[PageRefreshResult]
    changes: list[ChangeRecord]


class NotificationTestRequest(BaseModel):
    message: str = Field(default="EDB Agent webhook test", max_length=500)


class NotificationResult(BaseModel):
    status: Literal["sent", "skipped", "failed"]
    detail: str


class DemoMutationResponse(BaseModel):
    url: str
    title: str
    detail: str


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    database_ready: bool
    llm_configured: bool
    webhook_configured: bool
