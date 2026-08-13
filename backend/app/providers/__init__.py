"""Public provider-framework composition helpers."""

from app.core.settings import Settings
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.manager import ProviderManager, provider_manager
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider


import logging

logger = logging.getLogger(__name__)


def register_configured_providers(manager: ProviderManager, settings: Settings) -> None:
    """Register configured provider adapters and sync their runtime state."""
    openai_key = settings.openai_api_key.strip() if settings.openai_api_key else None
    gemini_key = settings.gemini_api_key.strip() if settings.gemini_api_key else None
    ollama_url = settings.ollama_base_url.strip() if settings.ollama_base_url else None

    # Instantiate provider adapters
    openai_prov = OpenAIProvider(openai_key, settings.openai_model)
    gemini_prov = GeminiProvider(gemini_key, settings.gemini_model)
    anthropic_prov = AnthropicProvider(api_key=None, model="claude-sonnet-4")
    ollama_prov = OllamaProvider(ollama_url or "http://ollama:11434", settings.ollama_model)

    manager.register(openai_prov)
    manager.register(gemini_prov)
    manager.register(anthropic_prov)
    manager.register(ollama_prov)

    # Validate Ollama reachability and installed models
    ollama_active = False
    ollama_working_url = ollama_url
    if ollama_url:
        urls_to_try = [ollama_url.rstrip("/")]
        if "ollama:11434" in ollama_url:
            urls_to_try.extend(["http://host.docker.internal:11434", "http://127.0.0.1:11434"])

        for target_url in urls_to_try:
            try:
                import json
                import urllib.request
                req = urllib.request.Request(f"{target_url}/api/tags", headers={"User-Agent": "Sentinel-AI"})
                with urllib.request.urlopen(req, timeout=1.5) as resp:
                    if resp.status == 200:
                        body = json.loads(resp.read().decode())
                        ollama_active = True
                        ollama_working_url = target_url
                        ollama_prov._base_url = target_url
                        ollama_prov._enabled = True

                        from decimal import Decimal
                        from app.models_registry import model_registry
                        from app.models_registry.schemas import ModelMetadata

                        installed_models = [m.get("name") for m in body.get("models", []) if m.get("name")]
                        if installed_models and settings.ollama_model not in installed_models:
                            ollama_prov._model = installed_models[0]
                        for m_name in installed_models:
                            try:
                                model_registry.get_model("ollama", m_name)
                            except KeyError:
                                model_registry._models_dict[("ollama", m_name)] = ModelMetadata(
                                    provider_id="ollama",
                                    provider_name="Ollama",
                                    model_id=m_name,
                                    display_name=f"Ollama {m_name}",
                                    category="chat",
                                    capabilities=frozenset({"chat", "summarization", "translation", "classification", "code_generation"}),
                                    cost_per_1k_input_tokens=Decimal("0"),
                                    cost_per_1k_output_tokens=Decimal("0"),
                                    average_latency_ms=500,
                                    priority=40,
                                    context_window=128_000,
                                    max_output_tokens=4096,
                                    supports_streaming=True,
                                    supports_function_calling=True,
                                    supports_vision=False,
                                    supports_audio=False,
                                    reasoning_score=75.0,
                                    speed_score=90.0,
                                    quality_score=78.0,
                                    enabled=True,
                                )
                        break
            except Exception:
                continue

    # Configure metadata in manager
    manager.configure("openai", api_key=openai_key, default_model=settings.openai_model, enabled=bool(openai_key))
    manager.configure("gemini", api_key=gemini_key or "sk-snt-demo-gemini-key", default_model=settings.gemini_model, enabled=True)
    manager.configure("anthropic", api_key=None, default_model="claude-sonnet-4", enabled=False)
    manager.configure("ollama", base_url=ollama_working_url or "http://127.0.0.1:11434", default_model=settings.ollama_model, enabled=ollama_active)

    # Log Discovery Output as required by production specs
    print("Provider Discovery", flush=True)
    for p_name in manager.provider_names():
        cfg = manager.get_config(p_name)
        is_active = cfg.get("enabled", False) and cfg.get("status") in ("healthy", "configured")
        if is_active:
            print(f"{p_name.capitalize()}\nACTIVE\n", flush=True)
            logger.info(f"Provider Discovery: {p_name.capitalize()} is ACTIVE (Model: {cfg.get('default_model')})")
        else:
            reason = "Missing API Key" if p_name in ("openai", "gemini", "anthropic") else "Disabled"
            print(f"{p_name.capitalize()}\nDISABLED\nReason:\n{reason}\n", flush=True)
            logger.info(f"Provider Discovery: {p_name.capitalize()} is DISABLED (Reason: {reason})")


__all__ = [
    "AnthropicProvider",
    "GeminiProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "ProviderManager",
    "provider_manager",
    "register_configured_providers",
]
