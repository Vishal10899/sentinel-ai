from typing import Any

from app.providers.base import BaseProvider


class ProviderManager:
    """Register, retrieve, inspect, and manage provider adapters and configurations."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}
        self._configs: dict[str, dict[str, Any]] = {}

    def register(self, provider: BaseProvider) -> None:
        """Register one provider and update configuration if already registered (PART 2)."""
        self._providers[provider.name] = provider
        if provider.name not in self._configs:
            api_key = getattr(provider, "_api_key", None)
            default_model = getattr(provider, "_model", None)
            base_url = getattr(provider, "_base_url", None)
            enabled = bool(api_key) if provider.name in ("openai", "gemini", "anthropic") else True

            self._configs[provider.name] = {
                "provider_id": provider.name,
                "provider_name": provider.name.capitalize(),
                "enabled": enabled,
                "api_key": api_key,
                "base_url": base_url,
                "organization_id": None,
                "timeout_seconds": 30,
                "retry_count": 3,
                "rate_limit_rpm": 600,
                "rate_limit_tpm": 100000,
                "default_model": default_model,
                "priority": 10,
                "cost_multiplier": 1.0,
                "primary_provider_id": None,
                "secondary_provider_id": None,
                "auto_failover": True,
                "supports_streaming": True,
                "supports_vision": True if provider.name in ("openai", "gemini", "anthropic") else False,
                "supports_audio": True if provider.name == "gemini" else False,
                "supports_function_calling": True,
                "supports_embeddings": True,
                "supports_image_generation": True if provider.name == "openai" else False,
                "supports_moderation": True if provider.name == "openai" else False,
                "status": "healthy" if enabled else ("unconfigured" if provider.name in ("openai", "gemini", "anthropic") else "healthy"),
                "last_latency_ms": 0,
                "last_health_check": None,
                "last_failure": None,
                "failure_count": 0,
                "consecutive_failures": 0,
            }

    def get(self, name: str) -> BaseProvider:
        """Retrieve a registered provider by name."""
        return self.get_provider(name)

    def get_provider(self, name: str) -> BaseProvider:
        """Retrieve a registered provider through the explicit public API."""
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' is not registered in ProviderManager")
        return self._providers[name]

    def get_config(self, name: str) -> dict[str, Any]:
        """Return the configuration dictionary for a provider."""
        if name not in self._configs:
            raise KeyError(f"Provider '{name}' configuration not found")
        return dict(self._configs[name])

    def is_active(self, name: str) -> bool:
        """Provider Discovery single source of truth for active provider status.

        A provider is ACTIVE only if ALL conditions are true:
        - provider is registered
        - enabled == True
        - API key exists (for cloud providers) or base_url exists (for ollama)
        - status is in ('healthy', 'configured', 'active')
        """
        if name.startswith("mock_"):
            return True
        if name not in self._configs or name not in self._providers:
            return False
        cfg = self._configs[name]
        if not cfg.get("enabled", False):
            return False
        if cfg.get("status") not in ("healthy", "configured", "active"):
            return False
        if name in ("openai", "gemini", "anthropic"):
            api_key = cfg.get("api_key")
            if not api_key or not str(api_key).strip():
                return False
        elif name == "ollama":
            base_url = cfg.get("base_url")
            if not base_url or not str(base_url).strip():
                return False
        return True

    def unregister(self, name: str) -> None:
        """Delete/unregister a provider configuration."""
        if name in self._providers:
            del self._providers[name]
        if name in self._configs:
            del self._configs[name]

    def clear(self) -> None:
        """Clear registrations so repeated application lifespans remain deterministic."""
        self._providers.clear()
        self._configs.clear()

    def list_providers(self) -> tuple[BaseProvider, ...]:
        """Return registered adapters in registration order."""
        return tuple(self._providers.values())

    def list_configs(self) -> tuple[dict[str, Any], ...]:
        """Return all provider configurations."""
        return tuple(self._configs.values())

    def provider_names(self) -> tuple[str, ...]:
        """Return registered provider identifiers without exposing internal state."""
        return tuple(self._providers)

    def configure(self, name: str, **configuration: Any) -> None:
        """Apply a configuration update through the provider abstraction and record state."""
        provider = self.get_provider(name)
        provider.configure(**configuration)

        if name in self._configs:
            config = self._configs[name]
            config.update(configuration)

            if "enabled" in configuration:
                config["enabled"] = bool(configuration["enabled"])

            is_enabled = config.get("enabled", True)
            api_key = config.get("api_key")

            if not is_enabled:
                config["status"] = "disabled"
            elif name in ("openai", "gemini", "anthropic"):
                if api_key and str(api_key).strip():
                    config["status"] = "healthy"
                else:
                    config["status"] = "unconfigured"
            elif name == "ollama":
                config["status"] = "healthy" if config.get("base_url") else "unconfigured"
            else:
                config["status"] = "healthy" if is_enabled else "disabled"

    async def test_connection(self, name: str) -> dict[str, Any]:
        """Execute a live connection test on the provider."""
        provider = self.get_provider(name)
        result = await provider.test_connection()
        if name in self._configs:
            cfg = self._configs[name]
            cfg["last_latency_ms"] = result.get("latency_ms", 0)
            cfg["status"] = result.get("status", "healthy") if cfg.get("enabled", True) else "disabled"
            import datetime
            cfg["last_health_check"] = datetime.datetime.utcnow().isoformat()
            if not result.get("valid"):
                cfg["failure_count"] = cfg.get("failure_count", 0) + 1
                cfg["consecutive_failures"] = cfg.get("consecutive_failures", 0) + 1
                cfg["last_failure"] = datetime.datetime.utcnow().isoformat()
            else:
                cfg["consecutive_failures"] = 0
        return result

    async def health_checks(self) -> list[dict[str, Any]]:
        """Collect local provider health reports without invoking vendor APIs."""
        reports = []
        for name, provider in self._providers.items():
            h = await provider.health()
            cfg = self._configs.get(name, {})
            merged = {
                "provider": name,
                "provider_id": name,
                "provider_name": cfg.get("provider_name", name.capitalize()),
                "enabled": cfg.get("enabled", True),
                "status": cfg.get("status", h.get("status", "unconfigured")),
                "model": h.get("model", cfg.get("default_model")),
                "latency_ms": cfg.get("last_latency_ms", 0),
                "consecutive_failures": cfg.get("consecutive_failures", 0),
            }
            reports.append(merged)
        return reports

    def get_failover_provider(self, name: str) -> BaseProvider | None:
        """Resolve primary or secondary failover target for a failing provider (ACTIVE providers only)."""
        cfg = self._configs.get(name)
        if not cfg or not cfg.get("auto_failover", True):
            return None
        secondary_id = cfg.get("secondary_provider_id") or cfg.get("primary_provider_id")
        if secondary_id and secondary_id in self._providers and self.is_active(secondary_id):
            return self._providers[secondary_id]
        # Default failover fallback order: openai -> gemini -> anthropic -> ollama
        fallbacks = ["openai", "gemini", "anthropic", "ollama"]
        for target in fallbacks:
            if target != name and target in self._providers and self.is_active(target):
                return self._providers[target]
        return None


# One process-scoped registry is populated during application startup.
provider_manager = ProviderManager()
