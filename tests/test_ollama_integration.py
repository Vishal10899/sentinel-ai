"""Production unit and integration tests for Sentinel AI Ollama Integration."""

import asyncio
import json
import pytest
from httpx import Response
from unittest.mock import AsyncMock, patch

from app.providers.ollama_provider import OllamaProvider
from app.providers.manager import ProviderManager
from app.models_registry import model_registry
from app.orchestration.router import AdaptiveRouter


def test_ollama_provider_test_connection_healthy():
    """Verify test_connection when Ollama is reachable."""
    async def _test():
        provider = OllamaProvider("http://localhost:11434", "llama3.2")
        mock_tags_response = Response(
            200,
            json={
                "models": [
                    {"name": "llama3.2:latest"},
                    {"name": "mistral:latest"},
                ]
            },
        )
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_tags_response
            res = await provider.test_connection()
            assert res["valid"] is True
            assert res["status"] == "healthy"
            assert "models" in res
            assert "llama3.2:latest" in res["models"]

    asyncio.run(_test())


def test_ollama_provider_test_connection_unconfigured():
    """Verify test_connection when base URL is unconfigured."""
    async def _test():
        provider = OllamaProvider("", "llama3.2")
        res = await provider.test_connection()
        assert isinstance(res["valid"], bool)

    asyncio.run(_test())


def test_ollama_provider_generate():
    """Verify generate sends correct payload and extracts response."""
    async def _test():
        provider = OllamaProvider("http://localhost:11434", "llama3.2")
        mock_res = Response(200, json={"response": "Hello from Ollama!"})

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_res
            text = await provider.generate("Hi", max_tokens=200, temperature=0.7)
            assert text == "Hello from Ollama!"
            
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args.kwargs
            assert "llama3.2" in call_kwargs["json"]["model"]
            assert call_kwargs["json"]["prompt"] == "Hi"
            assert call_kwargs["json"]["options"]["num_predict"] == 200
            assert call_kwargs["json"]["options"]["temperature"] == 0.7

    asyncio.run(_test())


def test_ollama_provider_embed():
    """Verify embed extracts vector embedding list."""
    async def _test():
        provider = OllamaProvider("http://localhost:11434", "llama3.2")
        expected_vec = [0.1, 0.2, 0.3, 0.4]
        mock_res = Response(200, json={"embeddings": [expected_vec]})

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_res
            vec = await provider.embed("sample text")
            assert vec == expected_vec

    asyncio.run(_test())


def test_ollama_provider_list_models():
    """Verify list_models fetches installed models."""
    async def _test():
        provider = OllamaProvider("http://localhost:11434", "llama3.2")
        mock_tags = Response(200, json={"models": [{"name": "llama3.2"}, {"name": "deepseek-r1"}]})

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_tags
            models = await provider.list_models()
            assert "llama3.2" in models
            assert "deepseek-r1" in models

    asyncio.run(_test())


def test_model_registry_dynamic_ollama_registration():
    """Verify ModelRegistry dynamically registers requested Ollama models on demand."""
    meta = model_registry.get_model("ollama", "custom-ollama-model-xyz")
    assert meta.provider_id == "ollama"
    assert meta.model_id == "custom-ollama-model-xyz"
    assert meta.cost_per_1k_input_tokens == 0
    assert meta.enabled is True


def test_ollama_provider_configure_toggle():
    """Verify configuring Ollama provider state."""
    provider = OllamaProvider("http://localhost:11434", "llama3.2")
    assert provider._enabled is True

    provider.configure(enabled=False)
    assert provider._enabled is False
    assert provider._base_url == "http://localhost:11434"

    provider.configure(enabled=True)
    assert provider._enabled is True

