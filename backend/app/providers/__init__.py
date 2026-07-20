"""Public provider-framework composition helpers."""

from app.core.settings import Settings
from app.providers.gemini_provider import GeminiProvider
from app.providers.manager import ProviderManager, provider_manager
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider


def register_configured_providers(manager: ProviderManager, settings: Settings) -> None:
    """Register configured provider adapters without creating network clients."""
    manager.register(OpenAIProvider(settings.openai_api_key, settings.openai_model))
    manager.register(GeminiProvider(settings.gemini_api_key, settings.gemini_model))
    manager.register(OllamaProvider(settings.ollama_base_url, settings.ollama_model))


__all__ = ["ProviderManager", "provider_manager", "register_configured_providers"]
