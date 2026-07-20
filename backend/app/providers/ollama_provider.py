"""Placeholder adapter for a future Ollama integration."""

from typing import Any

from app.providers.base import BaseProvider


class OllamaProvider(BaseProvider):
    """Store Ollama configuration while leaving all network calls unimplemented."""

    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url
        self._model = model

    @property
    def name(self) -> str:
        """Return the registry identifier for this adapter."""
        return "ollama"

    async def generate(self, prompt: str, **options: Any) -> str:
        """Placeholder for future text generation integration."""
        raise NotImplementedError("Ollama generation is not implemented")

    async def embed(self, text: str, **options: Any) -> list[float]:
        """Placeholder for future embedding integration."""
        raise NotImplementedError("Ollama embeddings are not implemented")

    async def health(self) -> dict[str, str]:
        """Report configured local endpoint details without contacting Ollama."""
        return {
            "provider": self.name,
            "status": "configured" if self._base_url else "not_configured",
            "model": self._model,
        }

    def configure(self, api_key=None, model=None, enabled=True) -> None:
        if model: self._model = model
        if not enabled: self._base_url = ""
