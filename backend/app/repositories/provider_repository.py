"""Repository for provider configuration persistence in PostgreSQL."""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provider import ProviderConfig
from app.providers.security import decrypt_secret, encrypt_secret, sanitize_base_url

logger = logging.getLogger(__name__)


class ProviderRepository:
    """Async database repository for managing ProviderConfig entity records."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> list[ProviderConfig]:
        """Fetch all provider configuration records from DB."""
        result = await self.db.execute(select(ProviderConfig))
        return list(result.scalars().all())

    async def get_by_id(self, provider_id: str) -> ProviderConfig | None:
        """Fetch a single provider configuration by provider_id."""
        result = await self.db.execute(select(ProviderConfig).where(ProviderConfig.provider_id == provider_id))
        return result.scalar_one_or_none()

    async def save_or_update(self, provider_id: str, config: dict[str, Any]) -> ProviderConfig:
        """Persist or update provider config record in database."""
        db_config = await self.get_by_id(provider_id)
        api_key = config.get("api_key")
        encrypted_key = encrypt_secret(api_key) if api_key else (db_config.api_key_encrypted if db_config else None)

        base_url = sanitize_base_url(
            config.get("base_url"),
            "https://api.anthropic.com" if provider_id == "anthropic" else ("http://127.0.0.1:11434" if provider_id == "ollama" else None),
        )

        if not db_config:
            db_config = ProviderConfig(
                provider_id=provider_id,
                provider_name=config.get("provider_name", provider_id.capitalize()),
                enabled=config.get("enabled", True),
                api_key_encrypted=encrypted_key,
                base_url=base_url,
                organization_id=config.get("organization_id"),
                timeout_seconds=config.get("timeout_seconds", 30),
                retry_count=config.get("retry_count", 3),
                rate_limit_rpm=config.get("rate_limit_rpm", 600),
                rate_limit_tpm=config.get("rate_limit_tpm", 100000),
                default_model=config.get("default_model") or config.get("model"),
                priority=config.get("priority", 10),
                cost_multiplier=config.get("cost_multiplier", 1.0),
                primary_provider_id=config.get("primary_provider_id"),
                secondary_provider_id=config.get("secondary_provider_id"),
                auto_failover=config.get("auto_failover", True),
                status=config.get("status", "healthy"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(db_config)
        else:
            if "provider_name" in config and config["provider_name"]:
                db_config.provider_name = config["provider_name"]
            if "enabled" in config:
                db_config.enabled = bool(config["enabled"])
            if api_key:
                db_config.api_key_encrypted = encrypted_key
            if "base_url" in config:
                db_config.base_url = base_url
            if "organization_id" in config:
                db_config.organization_id = config["organization_id"]
            if "timeout_seconds" in config:
                db_config.timeout_seconds = config["timeout_seconds"]
            if "retry_count" in config:
                db_config.retry_count = config["retry_count"]
            if "rate_limit_rpm" in config:
                db_config.rate_limit_rpm = config["rate_limit_rpm"]
            if "rate_limit_tpm" in config:
                db_config.rate_limit_tpm = config["rate_limit_tpm"]
            if "default_model" in config or "model" in config:
                db_config.default_model = config.get("default_model") or config.get("model")
            if "priority" in config:
                db_config.priority = config["priority"]
            if "cost_multiplier" in config:
                db_config.cost_multiplier = config["cost_multiplier"]
            if "primary_provider_id" in config:
                db_config.primary_provider_id = config["primary_provider_id"]
            if "secondary_provider_id" in config:
                db_config.secondary_provider_id = config["secondary_provider_id"]
            if "auto_failover" in config:
                db_config.auto_failover = config["auto_failover"]
            if "status" in config:
                db_config.status = config["status"]
            db_config.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(db_config)
        return db_config
