"""Enterprise Provider Registry & Model Catalog Manager."""

from collections.abc import Iterable
from types import MappingProxyType
import time

from app.models_registry.capability_matrix import capability_matrix_engine
from app.models_registry.catalog.default_catalog import DEFAULT_MODELS, DEFAULT_PROVIDERS
from app.models_registry.schemas import ModelMetadata, ProviderMetadata


class ModelRegistry:
    """Enterprise Single Source of Truth for Provider and Model Metadata."""

    def __init__(
        self,
        providers: Iterable[ProviderMetadata] = (),
        models: Iterable[ModelMetadata] = (),
    ) -> None:
        p_records = list(providers or DEFAULT_PROVIDERS)
        m_records = list(models or DEFAULT_MODELS)

        self._providers_dict: dict[str, ProviderMetadata] = {p.provider_id: p for p in p_records}
        self._models_dict: dict[tuple[str, str], ModelMetadata] = {
            (m.provider_id, m.model_id): m for m in m_records
        }
        self._preferred_models: set[tuple[str, str]] = set()

    def get_provider(self, provider: str) -> ProviderMetadata:
        """Return provider metadata by identifier (< 1ms)."""
        if provider not in self._providers_dict:
            raise KeyError(f"Provider '{provider}' is not registered.")
        return self._providers_dict[provider]

    def get_model(self, provider: str, model_name: str) -> ModelMetadata:
        """Return model metadata by composite key (< 1ms)."""
        key = (provider, model_name)
        if key not in self._models_dict:
            if provider.lower() == "ollama":
                from decimal import Decimal
                dynamic_meta = ModelMetadata(
                    provider_id="ollama",
                    provider_name="Ollama",
                    model_id=model_name,
                    display_name=f"Ollama {model_name}",
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
                self._models_dict[key] = dynamic_meta
                return dynamic_meta
            raise KeyError(f"Model '{provider}/{model_name}' is not registered.")
        return self._models_dict[key]

    def list_providers(self, *, enabled_only: bool = False) -> tuple[ProviderMetadata, ...]:
        """Return all registered providers."""
        providers = tuple(self._providers_dict.values())
        if enabled_only:
            return tuple(p for p in providers if p.enabled and p.status in ("healthy", "configured", "active"))
        return providers

    def list_models(
        self,
        *,
        provider: str | None = None,
        category: str | None = None,
        enabled_only: bool = False,
    ) -> tuple[ModelMetadata, ...]:
        """Return model catalog entries filtered by provider, category, or enabled state."""
        from app.providers.manager import provider_manager

        models = tuple(self._models_dict.values())
        if provider is not None:
            models = tuple(m for m in models if m.provider_id == provider)
        if category is not None:
            models = tuple(m for m in models if m.category.lower() == category.lower())
        if enabled_only:
            models = tuple(
                m for m in models
                if m.enabled and not m.deprecated and provider_manager.is_active(m.provider_id)
            )
        return models

    def get_capability_matrix(self) -> dict:
        """Return unified capability matrix for all models."""
        return capability_matrix_engine.generate_matrix(list(self._models_dict.values()))

    # ====================================================
    # Service-Layer Admin Operations
    # ====================================================

    def enable_provider(self, provider_id: str) -> ProviderMetadata:
        """Enable a provider in the registry."""
        p = self.get_provider(provider_id)
        updated = ProviderMetadata(
            provider_id=p.provider_id,
            provider_name=p.provider_name,
            enabled=True,
            status="healthy",
            provider_type=p.provider_type,
            supported_regions=p.supported_regions,
            available_models=p.available_models,
            capabilities=p.capabilities,
            default_model=p.default_model,
            priority=p.priority,
            supports_streaming=p.supports_streaming,
            supports_vision=p.supports_vision,
            supports_json_mode=p.supports_json_mode,
            supports_function_calling=p.supports_function_calling,
            supports_image_input=p.supports_image_input,
            supports_audio_input=p.supports_audio_input,
            supports_embeddings=p.supports_embeddings,
            supports_batch=p.supports_batch,
            supports_fine_tuning=p.supports_fine_tuning,
            supports_tool_calling=p.supports_tool_calling,
            supports_reasoning=p.supports_reasoning,
            supports_long_context=p.supports_long_context,
            max_context_window=p.max_context_window,
            max_output_tokens=p.max_output_tokens,
            rate_limits=p.rate_limits,
            concurrent_request_limits=p.concurrent_request_limits,
            timeout_defaults=p.timeout_defaults,
            retry_policy=p.retry_policy,
            auth_type=p.auth_type,
            health_status="healthy",
            circuit_breaker_status=p.circuit_breaker_status,
            current_availability=p.current_availability,
        )
        self._providers_dict[provider_id] = updated
        return updated

    def disable_provider(self, provider_id: str) -> ProviderMetadata:
        """Disable a provider in the registry."""
        p = self.get_provider(provider_id)
        updated = ProviderMetadata(
            provider_id=p.provider_id,
            provider_name=p.provider_name,
            enabled=False,
            status="disabled",
            provider_type=p.provider_type,
            supported_regions=p.supported_regions,
            available_models=p.available_models,
            capabilities=p.capabilities,
            default_model=p.default_model,
            priority=p.priority,
            supports_streaming=p.supports_streaming,
            supports_vision=p.supports_vision,
            supports_json_mode=p.supports_json_mode,
            supports_function_calling=p.supports_function_calling,
            supports_image_input=p.supports_image_input,
            supports_audio_input=p.supports_audio_input,
            supports_embeddings=p.supports_embeddings,
            supports_batch=p.supports_batch,
            supports_fine_tuning=p.supports_fine_tuning,
            supports_tool_calling=p.supports_tool_calling,
            supports_reasoning=p.supports_reasoning,
            supports_long_context=p.supports_long_context,
            max_context_window=p.max_context_window,
            max_output_tokens=p.max_output_tokens,
            rate_limits=p.rate_limits,
            concurrent_request_limits=p.concurrent_request_limits,
            timeout_defaults=p.timeout_defaults,
            retry_policy=p.retry_policy,
            auth_type=p.auth_type,
            health_status="disabled",
            circuit_breaker_status="open",
            current_availability=0.0,
        )
        self._providers_dict[provider_id] = updated
        return updated

    def deprecate_model(self, provider_id: str, model_id: str) -> ModelMetadata:
        """Mark a model in the catalog as deprecated."""
        m = self.get_model(provider_id, model_id)
        updated = ModelMetadata(
            provider_id=m.provider_id,
            provider_name=m.provider_name,
            model_id=m.model_id,
            display_name=m.display_name,
            capabilities=m.capabilities,
            cost_per_1k_input_tokens=m.cost_per_1k_input_tokens,
            cost_per_1k_output_tokens=m.cost_per_1k_output_tokens,
            average_latency_ms=m.average_latency_ms,
            priority=m.priority,
            context_window=m.context_window,
            category=m.category,
            max_output_tokens=m.max_output_tokens,
            release_version=m.release_version,
            family=m.family,
            supports_streaming=m.supports_streaming,
            supports_function_calling=m.supports_function_calling,
            supports_vision=m.supports_vision,
            supports_audio=m.supports_audio,
            supports_reasoning=m.supports_reasoning,
            supports_coding=m.supports_coding,
            supports_math=m.supports_math,
            json_reliability_score=m.json_reliability_score,
            function_calling_score=m.function_calling_score,
            embedding_quality_score=m.embedding_quality_score,
            reasoning_score=m.reasoning_score,
            speed_score=m.speed_score,
            quality_score=m.quality_score,
            cost_score=m.cost_score,
            popularity_score=m.popularity_score,
            recommended_use_cases=m.recommended_use_cases,
            enabled=False,
            deprecated=True,
            stable=False,
            enterprise_approved=m.enterprise_approved,
        )
        self._models_dict[(provider_id, model_id)] = updated
        return updated

    def mark_preferred_model(self, provider_id: str, model_id: str) -> bool:
        """Mark a model as tenant/workspace preferred."""
        key = (provider_id, model_id)
        if key not in self._models_dict:
            raise KeyError(f"Model '{provider_id}/{model_id}' not found.")
        self._preferred_models.add(key)
        return True

    def mark_enterprise_approved(self, provider_id: str, model_id: str, approved: bool = True) -> ModelMetadata:
        """Mark model enterprise governance approval flag."""
        m = self.get_model(provider_id, model_id)
        updated = ModelMetadata(
            provider_id=m.provider_id,
            provider_name=m.provider_name,
            model_id=m.model_id,
            display_name=m.display_name,
            capabilities=m.capabilities,
            cost_per_1k_input_tokens=m.cost_per_1k_input_tokens,
            cost_per_1k_output_tokens=m.cost_per_1k_output_tokens,
            average_latency_ms=m.average_latency_ms,
            priority=m.priority,
            context_window=m.context_window,
            category=m.category,
            max_output_tokens=m.max_output_tokens,
            release_version=m.release_version,
            family=m.family,
            supports_streaming=m.supports_streaming,
            supports_function_calling=m.supports_function_calling,
            supports_vision=m.supports_vision,
            supports_audio=m.supports_audio,
            supports_reasoning=m.supports_reasoning,
            supports_coding=m.supports_coding,
            supports_math=m.supports_math,
            json_reliability_score=m.json_reliability_score,
            function_calling_score=m.function_calling_score,
            embedding_quality_score=m.embedding_quality_score,
            reasoning_score=m.reasoning_score,
            speed_score=m.speed_score,
            quality_score=m.quality_score,
            cost_score=m.cost_score,
            popularity_score=m.popularity_score,
            recommended_use_cases=m.recommended_use_cases,
            enabled=m.enabled,
            deprecated=m.deprecated,
            stable=m.stable,
            enterprise_approved=approved,
        )
        self._models_dict[(provider_id, model_id)] = updated
        return updated

    def change_priority(self, provider_id: str, model_id: str, new_priority: int) -> ModelMetadata:
        """Change model execution priority in catalog."""
        m = self.get_model(provider_id, model_id)
        updated = ModelMetadata(
            provider_id=m.provider_id,
            provider_name=m.provider_name,
            model_id=m.model_id,
            display_name=m.display_name,
            capabilities=m.capabilities,
            cost_per_1k_input_tokens=m.cost_per_1k_input_tokens,
            cost_per_1k_output_tokens=m.cost_per_1k_output_tokens,
            average_latency_ms=m.average_latency_ms,
            priority=new_priority,
            context_window=m.context_window,
            category=m.category,
            max_output_tokens=m.max_output_tokens,
            release_version=m.release_version,
            family=m.family,
            supports_streaming=m.supports_streaming,
            supports_function_calling=m.supports_function_calling,
            supports_vision=m.supports_vision,
            supports_audio=m.supports_audio,
            supports_reasoning=m.supports_reasoning,
            supports_coding=m.supports_coding,
            supports_math=m.supports_math,
            json_reliability_score=m.json_reliability_score,
            function_calling_score=m.function_calling_score,
            embedding_quality_score=m.embedding_quality_score,
            reasoning_score=m.reasoning_score,
            speed_score=m.speed_score,
            quality_score=m.quality_score,
            cost_score=m.cost_score,
            popularity_score=m.popularity_score,
            recommended_use_cases=m.recommended_use_cases,
            enabled=m.enabled,
            deprecated=m.deprecated,
            stable=m.stable,
            enterprise_approved=m.enterprise_approved,
        )
        self._models_dict[(provider_id, model_id)] = updated
        return updated


model_registry = ModelRegistry()
