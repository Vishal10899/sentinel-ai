"""SQLAlchemy model for enterprise provider configurations and health states."""

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProviderConfig(Base):
    """Database model storing provider credentials, limits, features, and health statistics."""

    __tablename__ = "provider_configs"

    provider_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    provider_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    api_key_encrypted: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    base_url: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    organization_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )

    rate_limit_rpm: Mapped[int] = mapped_column(
        Integer,
        default=600,
        nullable=False,
    )

    rate_limit_tpm: Mapped[int] = mapped_column(
        Integer,
        default=100000,
        nullable=False,
    )

    default_model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    cost_multiplier: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )

    # Failover rules
    primary_provider_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    secondary_provider_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    auto_failover: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Capability / Feature flags
    supports_streaming: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    supports_vision: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    supports_audio: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    supports_function_calling: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    supports_embeddings: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    supports_image_generation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    supports_moderation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Health & SLA monitoring
    status: Mapped[str] = mapped_column(
        String(30),
        default="unconfigured",
        nullable=False,
    )

    last_latency_ms: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    last_health_check: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    last_failure: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    failure_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    consecutive_failures: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration safely for domain consumption."""
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "enabled": self.enabled,
            "base_url": self.base_url,
            "organization_id": self.organization_id,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "rate_limit_rpm": self.rate_limit_rpm,
            "rate_limit_tpm": self.rate_limit_tpm,
            "default_model": self.default_model,
            "priority": self.priority,
            "cost_multiplier": self.cost_multiplier,
            "primary_provider_id": self.primary_provider_id,
            "secondary_provider_id": self.secondary_provider_id,
            "auto_failover": self.auto_failover,
            "supports_streaming": self.supports_streaming,
            "supports_vision": self.supports_vision,
            "supports_audio": self.supports_audio,
            "supports_function_calling": self.supports_function_calling,
            "supports_embeddings": self.supports_embeddings,
            "supports_image_generation": self.supports_image_generation,
            "supports_moderation": self.supports_moderation,
            "status": self.status,
            "last_latency_ms": self.last_latency_ms,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "failure_count": self.failure_count,
            "consecutive_failures": self.consecutive_failures,
        }
