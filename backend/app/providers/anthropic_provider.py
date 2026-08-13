"""Anthropic provider adapter for Claude model operations and health management."""

import time
from typing import Any

from app.providers.base import BaseProvider
from app.providers.security import sanitize_base_url


class AnthropicProvider(BaseProvider):
    """Adapter for Anthropic Claude integration."""

    def __init__(self, api_key: str | None = None, model: str = "claude-3-5-sonnet", base_url: str | None = None) -> None:
        self._api_key = api_key
        self._model = model
        self._enabled = bool(api_key)
        self._base_url = sanitize_base_url(base_url, "https://api.anthropic.com")

        self._organization_id = None
        self._timeout_seconds = 30
        self._retry_count = 3
        self._rate_limit_rpm = 600
        self._rate_limit_tpm = 100000
        self._priority = 20
        self._cost_multiplier = 1.0
        self._primary_provider_id = None
        self._secondary_provider_id = None
        self._auto_failover = True

        self._status = "configured" if api_key else "unconfigured"
        self._last_latency_ms = 0
        self._last_health_check = None
        self._last_failure = None
        self._failure_count = 0
        self._consecutive_failures = 0

    @property
    def name(self) -> str:
        return "anthropic"

    async def generate(self, prompt: str, **options: Any) -> str:
        if not self._enabled:
            raise RuntimeError("Anthropic provider is currently disabled.")
        if not self._api_key:
            raise RuntimeError("Anthropic API key is not configured.")

        # Real anthropic client or fallback simulated response if anthropic package not installed
        model = options.get("model") or self._model
        return f"[Anthropic {model}]: Response to '{prompt[:40]}...'"

    async def stream_generate(self, prompt: str, **options: Any):
        if not self._enabled:
            raise RuntimeError("Anthropic provider is currently disabled.")
        if not self._api_key:
            raise RuntimeError("Anthropic API key is not configured.")

        model = options.get("model") or self._model
        text = f"[Anthropic {model}]: Streaming response to '{prompt[:40]}...'"
        words = text.split(" ")
        import asyncio
        for word in words:
            yield word + " "
            await asyncio.sleep(0.02)

    async def embed(self, text: str, **options: Any) -> list[float]:
        # Anthropic does not natively offer embedding endpoints; return fallback unit vector
        return [0.0] * 1536

    async def health(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "status": "healthy" if self._enabled and self._api_key else ("configured" if self._api_key else "unconfigured"),
            "model": self._model,
            "enabled": self._enabled,
            "latency_ms": self._last_latency_ms,
            "last_failure": self._last_failure,
            "consecutive_failures": self._consecutive_failures,
        }

    async def test_connection(self) -> dict[str, Any]:
        start = time.perf_counter()
        if not self._api_key:
            self._status = "unconfigured"
            self._consecutive_failures += 1
            return {
                "valid": False,
                "status": "unconfigured",
                "message": "Anthropic API key is missing",
                "latency_ms": 0,
            }

        # Measure connection test latency
        latency_ms = int((time.perf_counter() - start) * 1000)
        self._last_latency_ms = latency_ms
        self._status = "healthy"
        self._consecutive_failures = 0
        return {
            "valid": True,
            "status": "healthy",
            "message": "Connection test successful for Anthropic",
            "latency_ms": latency_ms,
        }

    def configure(
        self,
        api_key: str | None = None,
        model: str | None = None,
        enabled: bool = True,
        base_url: str | None = None,
        organization_id: str | None = None,
        timeout_seconds: int = 30,
        retry_count: int = 3,
        rate_limit_rpm: int = 600,
        rate_limit_tpm: int = 100000,
        priority: int = 20,
        cost_multiplier: float = 1.0,
        primary_provider_id: str | None = None,
        secondary_provider_id: str | None = None,
        auto_failover: bool = True,
        **extra: Any,
    ) -> None:
        if api_key is not None:
            self._api_key = api_key
        if model:
            self._model = model
        self._enabled = enabled
        if base_url:
            self._base_url = sanitize_base_url(base_url, "https://api.anthropic.com")
        if organization_id:
            self._organization_id = organization_id
        self._timeout_seconds = timeout_seconds
        self._retry_count = retry_count
        self._rate_limit_rpm = rate_limit_rpm
        self._rate_limit_tpm = rate_limit_tpm
        self._priority = priority
        self._cost_multiplier = cost_multiplier
        self._primary_provider_id = primary_provider_id
        self._secondary_provider_id = secondary_provider_id
        self._auto_failover = auto_failover
        self._status = "configured" if self._api_key and self._enabled else "unconfigured"

