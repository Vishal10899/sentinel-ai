"""Provider contract shared by every AI integration adapter."""

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """Abstract provider interface that keeps callers independent of vendors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable provider identifier used by the registry."""

    @abstractmethod
    async def generate(self, prompt: str, **options: Any) -> str:
        """Generate text from prompt using vendor API."""

    @abstractmethod
    async def stream_generate(self, prompt: str, **options: Any):
        """Stream generated token text chunks as an async generator."""

    @abstractmethod
    async def embed(self, text: str, **options: Any) -> list[float]:
        """Create vector embeddings for text."""

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """Report local configuration and health status metrics."""

    @abstractmethod
    async def test_connection(self) -> dict[str, Any]:
        """Execute a live verification request and return status with measured latency."""

    def configure(
        self,
        api_key: str | None = None,
        model: str | None = None,
        enabled: bool = True,
        base_url: str | None = None,
        organization_id: str | None = None,
        timeout_seconds: int = 30,
        retry_count: int = 3,
        rate_limit_rpm: int = 600,
        rate_limit_tpm: int = 100000,
        priority: int = 10,
        cost_multiplier: float = 1.0,
        primary_provider_id: str | None = None,
        secondary_provider_id: str | None = None,
        auto_failover: bool = True,
        **extra: Any,
    ) -> None:
        """Update provider runtime configuration without exposing implementation details."""
