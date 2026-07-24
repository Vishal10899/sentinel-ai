from typing import Any

from google import genai

from app.providers.base import BaseProvider


class GeminiProvider(BaseProvider):

    def __init__(self, api_key: str | None, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._client = genai.Client(api_key=api_key) if api_key else None

    @property
    def name(self) -> str:
        return "gemini"

    async def generate(self, prompt: str, **options: Any) -> str:

        if self._client is None:
            raise RuntimeError(
                "Gemini API key is not configured. "
                "Please set SENTINEL_AI_GEMINI_API_KEY in backend/.env."
            )

        model = options.get("model") or self._model
        print("Model sent to Gemini:", model)

        response = self._client.models.generate_content(
            model=model,
            contents=prompt,
        )

        return response.text or ""

    async def embed(self, text: str, **options: Any) -> list[float]:

        if self._client is None:
            raise RuntimeError(
                "Gemini API key is not configured. "
                "Please set SENTINEL_AI_GEMINI_API_KEY in backend/.env."
            )

        model = options.get("model") or "text-embedding-004"

        response = self._client.models.embed_content(
            model=model,
            contents=text,
        )

        return response.embeddings[0].values

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
            self._client = genai.Client(api_key=self._api_key)
        else:
            self._client = None