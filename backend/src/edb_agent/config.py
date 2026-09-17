from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL",
    )
    openrouter_model: str = Field(
        default="openai/gpt-5.4-mini",
        alias="OPENROUTER_MODEL",
    )
    openrouter_site_url: str = Field(
        default="http://localhost:3000",
        alias="OPENROUTER_SITE_URL",
    )
    openrouter_app_name: str = Field(
        default="EDB Primary Education Agent",
        alias="OPENROUTER_APP_NAME",
    )
    notification_webhook_url: str | None = Field(default=None, alias="NOTIFICATION_WEBHOOK_URL")
    source_seed_url: str = Field(
        default="https://www.edb.gov.hk/tc/edu-system/primary-secondary/primary.html",
        alias="SOURCE_SEED_URL",
    )
    cache_ttl_seconds: int = Field(default=300, ge=0, alias="CACHE_TTL_SECONDS")
    request_timeout_seconds: float = Field(default=20.0, gt=0, alias="REQUEST_TIMEOUT_SECONDS")
    retrieval_top_k: int = Field(default=5, ge=1, le=10, alias="RETRIEVAL_TOP_K")
    retrieval_min_score: float = Field(default=0.25, ge=0, alias="RETRIEVAL_MIN_SCORE")
    api_cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="API_CORS_ORIGINS",
    )
    demo_mode: bool = Field(default=False, alias="DEMO_MODE")
    data_dir: Path = Field(default=PROJECT_ROOT / "data", alias="DATA_DIR")

    @property
    def database_path(self) -> Path:
        return self.data_dir / "edb_agent.sqlite3"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
