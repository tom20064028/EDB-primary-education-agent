from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .agent import AgentService
from .config import get_settings
from .crawler import EDBCrawler, FetchFailure
from .models import (
    ChangeRecord,
    ChatRequest,
    ChatResponse,
    DemoMutationResponse,
    HealthResponse,
    NotificationResult,
    NotificationTestRequest,
    RefreshRequest,
    RefreshResponse,
    SourceSummary,
)
from .notifier import WebhookNotifier
from .retrieval import RetrievalService
from .service import SourceService
from .storage import Storage

settings = get_settings()
storage = Storage(settings.database_path)
crawler = EDBCrawler(settings.request_timeout_seconds)
notifier = WebhookNotifier(settings.notification_webhook_url, settings.request_timeout_seconds)
retrieval = RetrievalService(storage)
agent = AgentService(
    storage,
    retrieval,
    api_key=settings.openrouter_api_key,
    base_url=settings.openrouter_base_url,
    default_headers={
        "HTTP-Referer": settings.openrouter_site_url,
        "X-OpenRouter-Title": settings.openrouter_app_name,
    },
    model=settings.openrouter_model,
    top_k=settings.retrieval_top_k,
    min_score=settings.retrieval_min_score,
)
sources = SourceService(storage, crawler, notifier)
refresh_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    storage.initialize()
    yield


app = FastAPI(
    title="EDB Primary Education Agent API",
    description="Unofficial educational proof of concept using public EDB information.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        database_ready=settings.database_path.exists(),
        llm_configured=bool(settings.openrouter_api_key),
        webhook_configured=bool(settings.notification_webhook_url),
    )


@app.get("/api/sources", response_model=list[SourceSummary])
async def list_sources() -> list[SourceSummary]:
    return storage.list_sources()


@app.post("/api/sources/bootstrap", response_model=RefreshResponse)
async def bootstrap_sources() -> RefreshResponse:
    if refresh_lock.locked():
        raise HTTPException(status_code=409, detail="A source operation is already running")
    async with refresh_lock:
        try:
            return await sources.bootstrap(settings.source_seed_url)
        except FetchFailure as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/sources/refresh", response_model=RefreshResponse)
async def refresh_sources(request: RefreshRequest) -> RefreshResponse:
    if refresh_lock.locked():
        raise HTTPException(status_code=409, detail="A source operation is already running")
    if not storage.list_allowlist():
        raise HTTPException(status_code=409, detail="Initialize the source cache first")
    async with refresh_lock:
        return await sources.refresh(notify=request.notify)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not storage.all_chunks():
        raise HTTPException(status_code=409, detail="Initialize the source cache first")
    try:
        return await agent.answer(request.question)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="The language model request failed") from exc


@app.get("/api/changes", response_model=list[ChangeRecord])
async def list_changes(limit: int = Query(default=20, ge=1, le=100)) -> list[ChangeRecord]:
    return storage.list_changes(limit)


@app.post("/api/demo/mutate-snapshot", response_model=DemoMutationResponse)
async def mutate_snapshot() -> DemoMutationResponse:
    try:
        return sources.inject_demo_change()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/notifications/test", response_model=NotificationResult)
async def test_notification(request: NotificationTestRequest) -> NotificationResult:
    return await notifier.send(title="EDB Agent test", message=request.message)
