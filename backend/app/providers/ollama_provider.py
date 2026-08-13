from typing import Any

import httpx

from app.providers.base import BaseProvider
from app.providers.security import sanitize_base_url


class OllamaProvider(BaseProvider):
    def __init__(self, base_url: str | None, model: str) -> None:
        clean_url = sanitize_base_url(base_url, "http://127.0.0.1:11434")
        self._base_url = clean_url.rstrip("/") if clean_url else ""
        self._model = model
        self._enabled = bool(self._base_url)
        self._client: httpx.AsyncClient | None = None


    def _get_client(self, timeout: httpx.Timeout) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
            self._client = httpx.AsyncClient(timeout=timeout, limits=limits)
        return self._client

    @property
    def name(self) -> str:
        return "ollama"

    async def _resolve_model_name(self, requested_model: str | None) -> str:
        target = requested_model or self._model
        available = await self.list_models()
        if not available:
            return target
        if target in available:
            return target
        for tag in available:
            if tag.startswith(f"{target}:") or tag.split(":")[0] == target:
                return tag
        return available[0]

    async def generate(self, prompt: str, **options: Any) -> str:
        if not self._enabled or not self._base_url:
            raise RuntimeError("Ollama base URL is not configured.")

        model = await self._resolve_model_name(options.get("model") or self._model)
        output_tokens = options.get("max_tokens") or options.get("output_tokens", 100)
        temperature = options.get("temperature")
        messages = options.get("messages")

        payload_options: dict[str, Any] = {
            "num_predict": output_tokens,
            "num_ctx": options.get("num_ctx", 4096),
        }
        if temperature is not None:
            payload_options["temperature"] = temperature

        timeout = httpx.Timeout(600.0, connect=5.0)
        client = self._get_client(timeout)

        if messages:
            endpoint = f"{self._base_url}/api/chat"
            json_payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": payload_options,
                "keep_alive": "24h",
            }
        else:
            endpoint = f"{self._base_url}/api/generate"
            json_payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": payload_options,
                "keep_alive": "24h",
            }

        response = await client.post(endpoint, json=json_payload)

        if response.status_code != 200:
            raise RuntimeError(
                f"Ollama Error {response.status_code}\n"
                f"URL: {response.request.url}\n"
                f"Response: {response.text}"
            )

        data = response.json()
        if "message" in data and isinstance(data["message"], dict):
            return data["message"].get("content", "")
        return data.get("response", "")

    async def stream_generate(self, prompt: str, **options: Any):
        if not self._enabled or not self._base_url:
            raise RuntimeError("Ollama base URL is not configured.")

        model = await self._resolve_model_name(options.get("model") or self._model)
        output_tokens = options.get("max_tokens") or options.get("output_tokens")
        temperature = options.get("temperature")
        messages = options.get("messages")

        payload_options: dict[str, Any] = {
            "num_ctx": options.get("num_ctx", 4096),
        }
        if output_tokens is not None:
            payload_options["num_predict"] = output_tokens
        if temperature is not None:
            payload_options["temperature"] = temperature

        if messages:
            endpoint = f"{self._base_url}/api/chat"
            json_payload: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "stream": True,
                "keep_alive": "24h",
            }
        else:
            endpoint = f"{self._base_url}/api/generate"
            json_payload: dict[str, Any] = {
                "model": model,
                "prompt": prompt,
                "stream": True,
                "keep_alive": "24h",
            }
        if payload_options:
            json_payload["options"] = payload_options

        timeout = httpx.Timeout(120.0, read=120.0, connect=15.0)
        client = self._get_client(timeout)

        async with client.stream("POST", endpoint, json=json_payload) as response:
            if response.status_code == 404:
                err_text = await response.aread()
                err_str = err_text.decode("utf-8", "ignore")
                # Try auto-pulling the model tag
                try:
                    pull_res = await client.post(
                        f"{self._base_url}/api/pull",
                        json={"name": model, "stream": False},
                        timeout=httpx.Timeout(300.0, read=300.0, connect=15.0),
                    )
                    if pull_res.status_code == 200:
                        async with client.stream("POST", endpoint, json=json_payload) as retry_res:
                            if retry_res.status_code == 200:
                                import json
                                async for line in retry_res.aiter_lines():
                                    if line:
                                        try:
                                            payload = json.loads(line)
                                            chunk = payload.get("message", {}).get("content", "") if isinstance(payload.get("message"), dict) else payload.get("response", "")
                                            if chunk:
                                                yield chunk
                                        except Exception:
                                            continue
                                return
                except Exception:
                    pass
                raise RuntimeError(f"Ollama model '{model}' is not pulled in Ollama server container. Run 'docker exec -it sentinel-ai-ollama ollama pull {model}' to download it ({err_str}).")
            elif response.status_code != 200:
                err_text = await response.aread()
                err_str = err_text.decode("utf-8", "ignore")
                raise RuntimeError(f"Ollama stream error {response.status_code}: {err_str}")

            import json
            async for line in response.aiter_lines():
                if line:
                    try:
                        payload = json.loads(line)
                        chunk = payload.get("message", {}).get("content", "") if isinstance(payload.get("message"), dict) else payload.get("response", "")
                        if chunk:
                            yield chunk
                    except Exception:
                        continue

    async def embed(self, text: str, **options: Any) -> list[float]:
        if not self._enabled or not self._base_url:
            raise RuntimeError("Ollama base URL is not configured.")

        model = options.get("model") or self._model

        timeout = httpx.Timeout(600.0, connect=5.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            # Try primary /api/embed endpoint
            response = await client.post(
                f"{self._base_url}/api/embed",
                json={
                    "model": model,
                    "input": text,
                },
            )

            if response.status_code == 200:
                data = response.json()
                embeddings = data.get("embeddings")
                if embeddings and isinstance(embeddings, list) and len(embeddings) > 0:
                    return embeddings[0]
                if "embedding" in data:
                    return data["embedding"]
                return []

            # Fallback to legacy /api/embeddings endpoint
            legacy_response = await client.post(
                f"{self._base_url}/api/embeddings",
                json={
                    "model": model,
                    "prompt": text,
                },
            )

            if legacy_response.status_code == 200:
                data = legacy_response.json()
                return data.get("embedding", [])

            raise RuntimeError(
                f"Ollama Embed Error {response.status_code}\n"
                f"URL: {response.request.url}\n"
                f"Response: {response.text}"
            )

    async def list_models(self) -> list[str]:
        if not self._enabled or not self._base_url:
            return []
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self._base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    return [m.get("name") for m in data.get("models", []) if m.get("name")]
        except Exception:
            pass
        return []

    async def health(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "status": "healthy" if (self._enabled and self._base_url) else ("disabled" if not self._enabled else "unconfigured"),
            "model": self._model,
        }

    async def test_connection(self) -> dict[str, Any]:
        import time
        start = time.perf_counter()
        if not self._enabled or not self._base_url:
            return {
                "valid": False,
                "status": "unconfigured" if not self._base_url else "disabled",
                "message": "Ollama base URL is not configured or provider is disabled.",
                "latency_ms": 0,
            }
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self._base_url}/api/tags")
                latency_ms = int((time.perf_counter() - start) * 1000)
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", []) if m.get("name")]
                    return {
                        "valid": True,
                        "status": "healthy",
                        "message": f"Ollama server is reachable and active. ({len(models)} model(s) available)",
                        "models": models,
                        "latency_ms": latency_ms,
                    }
                return {
                    "valid": False,
                    "status": "degraded",
                    "message": f"Ollama returned HTTP status {res.status_code}",
                    "latency_ms": latency_ms,
                }
        except Exception as err:
            return {
                "valid": False,
                "status": "unhealthy",
                "message": f"Connection failed to Ollama: {err}",
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
        if base_url is not None:
            clean_url = sanitize_base_url(base_url, "http://127.0.0.1:11434")
            self._base_url = clean_url.rstrip("/") if clean_url else ""
        if model:
            self._model = model

        self._enabled = bool(enabled and self._base_url)
        self._client = None