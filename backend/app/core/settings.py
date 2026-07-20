"""Typed application configuration sourced from the environment."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for application metadata and transport concerns."""

    project_title: str = "Sentinel AI"
    project_version: str = "1.0.0"
    project_description: str = "Sentinel AI API service."
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    log_format: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    # The async PostgreSQL URL is consumed only by the database infrastructure.
    database_url: str = "postgresql+asyncpg://sentinel:sentinel@postgres:5432/sentinel_ai"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Redis is available as shared infrastructure but has no caching policy yet.
    redis_url: str = "redis://redis:6379/0"

    # Provider settings define future integrations; this foundation makes no API calls.
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"

    cors_origins: list[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    jwt_secret: str = "change-me-in-production"
    jwt_access_token_minutes: int = 30
    jwt_refresh_token_days: int = 14

    # Local development may override defaults with backend/.env. Environment
    # variables take precedence and use the SENTINEL_AI_ prefix.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SENTINEL_AI_",
    )


# Share one immutable-style settings object across application layers.
settings = Settings()
