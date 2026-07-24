from typing import Any

from openai import AsyncOpenAI

from app.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str | None, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key) if api_key else None

    @property
    def name(self) -> str:
        return "openai"

    async def generate(self, prompt: str, **options: Any) -> str:

        if self._client is None:
            raise RuntimeError("OpenAI API key is not configured.")

        model = options.get("model") or self._model

        response = await self._client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response.choices[0].message.content or ""

    async def embed(self, text: str, **options: Any) -> list[float]:

        if self._client is None:
            raise RuntimeError("OpenAI API key is not configured.")

        model = options.get("model") or "text-embedding-3-small"

        response = await self._client.embeddings.create(
            model=model,
            input=text,
        )

        return response.data[0].embedding

    async def health(self) -> dict[str, str]:
        return {
            "provider": self.name,
            "status": "configured" if self._api_key else "not_configured",
            "model": self._model,
        }

    def configure(
        self,
        api_key: str | None = None,
        model: str | None = None,
        enabled: bool = True,
    ) -> None:

        if api_key is not None:
            self._api_key = api_key

        if model:
            self._model = model

        if enabled and self._api_key:
            self._client = AsyncOpenAI(api_key=self._api_key)
        else:
            self._client = None