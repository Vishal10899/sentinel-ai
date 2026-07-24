from typing import Any

import httpx

from app.providers.base import BaseProvider


class OllamaProvider(BaseProvider):
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    @property
    def name(self) -> str:
        return "ollama"

    async def generate(self, prompt: str, **options: Any) -> str:
        model = options.get("model") or self._model
        output_tokens = options.get("output_tokens", 100)

        timeout = httpx.Timeout(
            connect=30.0,
            read=600.0,
            write=30.0,
            pool=30.0,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": output_tokens,
                    },
                },
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Ollama Error {response.status_code}\n"
                    f"URL: {response.request.url}\n"
                    f"Response: {response.text}"
                )

            data = response.json()
            return data.get("response", "")

    async def embed(self, text: str, **options: Any) -> list[float]:
        model = options.get("model") or self._model

        timeout = httpx.Timeout(
            connect=30.0,
            read=600.0,
            write=30.0,
            pool=30.0,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/embed",
                json={
                    "model": model,
                    "input": text,
                },
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Ollama Embed Error {response.status_code}\n"
                    f"URL: {response.request.url}\n"
                    f"Response: {response.text}"
                )

            data = response.json()
            return data.get("embeddings", [[]])[0]

    async def health(self) -> dict[str, str]:
        return {
            "provider": self.name,
            "status": "configured" if self._base_url else "not_configured",
            "model": self._model,
        }

    def configure(
        self,
        api_key: str | None = None,
        model: str | None = None,
        enabled: bool = True,
    ) -> None:
        if model:
            self._model = model

        if not enabled:
            self._base_url = ""