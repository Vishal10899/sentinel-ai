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
        """Generate text; concrete API behavior will be added in a later milestone."""

    @abstractmethod
    async def embed(self, text: str, **options: Any) -> list[float]:
        """Create embeddings; concrete API behavior will be added in a later milestone."""

    @abstractmethod
    async def health(self) -> dict[str, str]:
        """Report local configuration health without making a provider API request."""

    def configure(self, api_key: str | None = None, model: str | None = None, enabled: bool = True) -> None:
        """Update provider runtime configuration without exposing implementation details."""
