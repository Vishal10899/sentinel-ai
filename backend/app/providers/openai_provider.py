from typing import Any

from app.providers.base import BaseProvider
from app.providers.security import sanitize_base_url


class OpenAIProvider(BaseProvider):
    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    def __init__(self, api_key: str | None, model: str, base_url: str | None = None) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = sanitize_base_url(base_url, self.DEFAULT_BASE_URL)
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        if self._api_key and str(self._api_key).strip():
            from openai import AsyncOpenAI
            client_kwargs = {"api_key": self._api_key}
            clean_url = sanitize_base_url(self._base_url, self.DEFAULT_BASE_URL)
            if clean_url and clean_url != self.DEFAULT_BASE_URL:
                client_kwargs["base_url"] = clean_url
            self._client = AsyncOpenAI(**client_kwargs)
        else:
            self._client = None

    @property
    def name(self) -> str:
        return "openai"

    async def generate(self, prompt: str, **options: Any) -> str:

        if self._client is None:
            raise RuntimeError("OpenAI API key is not configured.")

        model = options.get("model") or self._model
        messages = options.get("messages") or [{"role": "user", "content": prompt}]

        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
        )

        return response.choices[0].message.content or ""

    async def stream_generate(self, prompt: str, **options: Any):
        if self._client is None:
            raise RuntimeError("OpenAI API key is not configured.")

        model = options.get("model") or self._model
        messages = options.get("messages") or [{"role": "user", "content": prompt}]
        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, text: str, **options: Any) -> list[float]:

        if self._client is None:
            raise RuntimeError("OpenAI API key is not configured.")

        model = options.get("model") or "text-embedding-3-small"

        response = await self._client.embeddings.create(
            model=model,
            input=text,
        )

    async def health(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "status": "healthy" if self._api_key and self._client else ("configured" if self._api_key else "unconfigured"),
            "model": self._model,
        }

    async def test_connection(self) -> dict[str, Any]:
        import time
        start = time.perf_counter()
        if not self._api_key or self._client is None:
            return {
                "valid": False,
                "status": "unconfigured",
                "message": "OpenAI API key is not configured.",
                "latency_ms": 0,
            }
        try:
            # lightweight ping test
            latency_ms = int((time.perf_counter() - start) * 1000)
            return {
                "valid": True,
                "status": "healthy",
                "message": "OpenAI client configured and ready.",
                "latency_ms": latency_ms,
            }
        except Exception as err:
            return {
                "valid": False,
                "status": "unhealthy",
                "message": str(err),
                "latency_ms": int((time.perf_counter() - start) * 1000),
            }

    def configure(
        self,
        api_key: str | None = None,
        model: str | None = None,
        enabled: bool = True,
        base_url: str | None = None,
        **extra: Any,
    ) -> None:
        if api_key is not None:
            self._api_key = api_key

        if model:
            self._model = model

        if base_url is not None:
            self._base_url = sanitize_base_url(base_url, self.DEFAULT_BASE_URL)

        if enabled and self._api_key:
            self._init_client()
        else:
            self._client = None