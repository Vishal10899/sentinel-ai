"""Typed application configuration sourced from the environment."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_env_file_paths = [
    str(Path(__file__).resolve().parent.parent.parent / ".env"),
    ".env",
]

class Settings(BaseSettings):
    """Runtime settings for application metadata and transport concerns."""

    project_title: str = "Sentinel AI"
    project_version: str = "1.0.0"
    project_description: str = "Sentinel AI API service."
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    log_format: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    # The async PostgreSQL URL is consumed only by the database infrastructure.
    database_url: str = "postgresql+asyncpg://sentinel:sentinel@postgres:5432/sentinel_ai"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    @property
    def async_database_url(self) -> str:
        return self.database_url

    # Redis is available as shared infrastructure but has no caching policy yet.
    redis_url: str = "redis://redis:6379/0"

    # Provider settings define future integrations.
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "tinyllama"

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    jwt_secret: str = "change-me-in-production"
    jwt_access_token_minutes: int = 30
    jwt_refresh_token_days: int = 14

    bootstrap_admin_email: str = "admin@sentinel.ai"
    bootstrap_admin_password: str = "admin123"

    bootstrap_super_admin_email_1: str = "Vishalkumar75912@gmail.com"
    bootstrap_super_admin_password_1: str | None = None
    bootstrap_super_admin_name_1: str = "Vishal Kumar"

    bootstrap_super_admin_email_2: str = "Vishalchaudhary74096@gmail.com"
    bootstrap_super_admin_password_2: str | None = None
    bootstrap_super_admin_name_2: str = "Vishal Chaudhary"
    bootstrap_super_admin_title_2: str = "Founder"

    @property
    def super_admin_emails(self) -> list[str]:
        raw = [
            self.bootstrap_admin_email,
            self.bootstrap_super_admin_email_1,
            self.bootstrap_super_admin_email_2,
        ]
        return [e.strip().lower() for e in raw if e and isinstance(e, str) and e.strip()]

    def is_super_admin_email(self, email: str | None) -> bool:
        if not email or not isinstance(email, str):
            return False
        return email.strip().lower() in self.super_admin_emails

    def model_post_init(self, __context) -> None:
        import os
        if not self.gemini_api_key:
            self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not self.openai_api_key:
            self.openai_api_key = os.environ.get("OPENAI_API_KEY")

        # Support non-prefixed environment variable overrides for Super Admins
        self.bootstrap_super_admin_email_1 = os.environ.get("BOOTSTRAP_SUPER_ADMIN_EMAIL_1", self.bootstrap_super_admin_email_1)
        self.bootstrap_super_admin_password_1 = os.environ.get("BOOTSTRAP_SUPER_ADMIN_PASSWORD_1", self.bootstrap_super_admin_password_1)
        self.bootstrap_super_admin_name_1 = os.environ.get("BOOTSTRAP_SUPER_ADMIN_NAME_1", self.bootstrap_super_admin_name_1)

        self.bootstrap_super_admin_email_2 = os.environ.get("BOOTSTRAP_SUPER_ADMIN_EMAIL_2", self.bootstrap_super_admin_email_2)
        self.bootstrap_super_admin_password_2 = os.environ.get("BOOTSTRAP_SUPER_ADMIN_PASSWORD_2", self.bootstrap_super_admin_password_2)
        self.bootstrap_super_admin_name_2 = os.environ.get("BOOTSTRAP_SUPER_ADMIN_NAME_2", self.bootstrap_super_admin_name_2)
        self.bootstrap_super_admin_title_2 = os.environ.get("BOOTSTRAP_SUPER_ADMIN_TITLE_2", self.bootstrap_super_admin_title_2)

    # Local development may override defaults with backend/.env. Environment
    # variables take precedence and use the SENTINEL_AI_ prefix.
    model_config = SettingsConfigDict(
        env_file=_env_file_paths,
        env_file_encoding="utf-8",
        env_prefix="SENTINEL_AI_",
        extra="ignore",
    )


# Share one immutable-style settings object across application layers.
settings = Settings()
