from edb_agent.config import Settings


def test_default_cors_origins_cover_common_local_hosts(monkeypatch) -> None:
    monkeypatch.delenv("API_CORS_ORIGINS", raising=False)

    settings = Settings(_env_file=None)

    assert settings.cors_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_default_llm_provider_is_openrouter(monkeypatch) -> None:
    for name in (
        "OPENROUTER_API_KEY",
        "OPENROUTER_BASE_URL",
        "OPENROUTER_MODEL",
        "OPENROUTER_SITE_URL",
        "OPENROUTER_APP_NAME",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.openrouter_api_key is None
    assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"
    assert settings.openrouter_model == "openai/gpt-5.4-mini"
    assert settings.openrouter_site_url == "http://localhost:3000"
    assert settings.openrouter_app_name == "EDB Primary Education Agent"
