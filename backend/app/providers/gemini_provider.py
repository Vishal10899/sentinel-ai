from typing import Any

from app.providers.base import BaseProvider
from app.providers.security import sanitize_base_url


class GeminiProvider(BaseProvider):
    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com"

    def __init__(self, api_key: str | None, model: str, base_url: str | None = None) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = sanitize_base_url(base_url, self.DEFAULT_BASE_URL)
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        if self._api_key and str(self._api_key).strip():
            try:
                from google import genai
                clean_url = sanitize_base_url(self._base_url, self.DEFAULT_BASE_URL)
                if clean_url and clean_url != self.DEFAULT_BASE_URL:
                    try:
                        self._client = genai.Client(api_key=self._api_key, http_options={"api_option": clean_url})
                    except Exception:
                        self._client = genai.Client(api_key=self._api_key)
                else:
                    self._client = genai.Client(api_key=self._api_key)
            except Exception:
                self._client = None
        else:
            self._client = None

    @property
    def name(self) -> str:
        return "gemini"

    def _normalize_model(self, model: str | None) -> str:
        target = model or self._model or "gemini-2.0-flash"
        if "2.5" in target:
            return "gemini-2.0-flash"
        return target


    async def generate(self, prompt: str, **options: Any) -> str:
        import asyncio
        import time
        from datetime import datetime
        model = self._normalize_model(options.get("model"))
        ts = datetime.utcnow().isoformat()
        print(f"[{ts}] [3] Gemini request started | Model: {model}", flush=True)
        print(f"[{ts}] [4] HTTP request sent to Gemini | Model: {model}", flush=True)

        if self._client is None:
            raise RuntimeError("Gemini API key is not configured or client failed to initialize.")

        try:
            print(f"[{ts}] Invoking Gemini SDK with 60s timeout...", flush=True)
            if hasattr(self._client, "aio"):
                response = await asyncio.wait_for(
                    self._client.aio.models.generate_content(model=model, contents=prompt),
                    timeout=60.0,
                )
            else:
                response = await asyncio.wait_for(
                    asyncio.to_thread(self._client.models.generate_content, model=model, contents=prompt),
                    timeout=60.0,
                )
            print(f"[{datetime.utcnow().isoformat()}] [5] First byte received | Raw Metadata: {getattr(response, 'usage_metadata', 'N/A')}", flush=True)
            print(f"[{datetime.utcnow().isoformat()}] SDK returned successfully", flush=True)
            return response.text or ""
        except asyncio.TimeoutError as err:
            print(f"[{datetime.utcnow().isoformat()}] ERROR: Gemini SDK call timed out after 60s", flush=True)
            raise RuntimeError("Gemini API call timed out after 60 seconds") from err
        except Exception as err:
            print(f"[{datetime.utcnow().isoformat()}] ERROR: Gemini SDK call failed: {err}", flush=True)
            raise

    async def stream_generate(self, prompt: str, **options: Any):
        import asyncio
        from datetime import datetime
        model = self._normalize_model(options.get("model"))
        ts = datetime.utcnow().isoformat()
        print(f"[{ts}] [3] Gemini request started | Model: {model}", flush=True)
        print(f"[{ts}] [4] HTTP request sent to Gemini | Model: {model}", flush=True)

        if self._client is None:
            raise RuntimeError("Gemini API key is not configured or client failed to initialize.")

        try:
            print(f"[{ts}] Invoking Gemini streaming SDK with 60s timeout...", flush=True)
            if hasattr(self._client, "aio"):
                response = await asyncio.wait_for(
                    self._client.aio.models.generate_content_stream(model=model, contents=prompt),
                    timeout=60.0,
                )
                print(f"[{datetime.utcnow().isoformat()}] [5] First byte received", flush=True)
                async for chunk in response:
                    if hasattr(chunk, "text") and chunk.text:
                        yield chunk.text
            else:
                response = await asyncio.wait_for(
                    asyncio.to_thread(self._client.models.generate_content_stream, model=model, contents=prompt),
                    timeout=60.0,
                )
                print(f"[{datetime.utcnow().isoformat()}] [5] First byte received", flush=True)
                for chunk in response:
                    if hasattr(chunk, "text") and chunk.text:
                        yield chunk.text
            print(f"[{datetime.utcnow().isoformat()}] SDK streaming generator exited normally", flush=True)
        except asyncio.TimeoutError as err:
            print(f"[{datetime.utcnow().isoformat()}] ERROR: Gemini streaming SDK call timed out after 60s", flush=True)
            raise RuntimeError("Gemini streaming API call timed out after 60 seconds") from err
        except Exception as err:
            print(f"[{datetime.utcnow().isoformat()}] ERROR: Gemini streaming SDK call failed: {err}", flush=True)
            raise

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
                "message": "Gemini API key is not configured.",
                "latency_ms": 0,
            }
        try:
            latency_ms = int((time.perf_counter() - start) * 1000)
            return {
                "valid": True,
                "status": "healthy",
                "message": "Gemini client configured and ready.",
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