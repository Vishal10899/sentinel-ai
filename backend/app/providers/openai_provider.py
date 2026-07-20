"""Placeholder adapter for a future OpenAI integration."""

from typing import Any

from app.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    """Store OpenAI configuration while leaving all vendor calls unimplemented."""

    def __init__(self, api_key: str | None, model: str) -> None:
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        """Return the registry identifier for this adapter."""
        return "openai"

    async def generate(self, prompt: str, **options: Any) -> str:
        """Placeholder for future text generation integration."""
        raise NotImplementedError("OpenAI generation is not implemented")

    async def embed(self, text: str, **options: Any) -> list[float]:
        """Placeholder for future embedding integration."""
        raise NotImplementedError("OpenAI embeddings are not implemented")

    async def health(self) -> dict[str, str]:
        """Report whether local configuration is present without contacting OpenAI."""
        status = "configured" if self._api_key else "not_configured"
        return {"provider": self.name, "status": status, "model": self._model}

    def configure(self, api_key=None, model=None, enabled=True) -> None:
        if api_key is not None: self._api_key = api_key
        if model: self._model = model
        if not enabled: self._api_key = None
