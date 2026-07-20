"""Read-only registry for provider and model infrastructure metadata."""

from collections.abc import Iterable
from types import MappingProxyType

from app.models_registry.schemas import ModelMetadata, ProviderMetadata


class ModelRegistry:
    """Expose immutable provider and model metadata to application consumers."""

    def __init__(
        self,
        providers: Iterable[ProviderMetadata] = (),
        models: Iterable[ModelMetadata] = (),
    ) -> None:
        provider_records = tuple(providers)
        model_records = tuple(models)
        provider_map = {
            provider.provider_id: provider for provider in provider_records
        }
        model_map = {
            (model.provider_id, model.model_id): model
            for model in model_records
        }

        if len(provider_map) != len(provider_records):
            raise ValueError("Provider identifiers must be unique")
        if len(model_map) != len(model_records):
            raise ValueError("Provider and model name pairs must be unique")
        if unknown_providers := {
            model.provider_id
            for model in model_map.values()
            if model.provider_id not in provider_map
        }:
            raise ValueError(f"Models reference unknown providers: {sorted(unknown_providers)}")

        # Mapping proxies prevent consumers from mutating registry state.
        self._providers = MappingProxyType(provider_map)
        self._models = MappingProxyType(model_map)

    def get_provider(self, provider: str) -> ProviderMetadata:
        """Return provider metadata by identifier."""
        return self._providers[provider]

    def get_model(self, provider: str, model_name: str) -> ModelMetadata:
        """Return model metadata by its provider and model-name composite key."""
        return self._models[(provider, model_name)]

    def list_providers(self, *, enabled_only: bool = False) -> tuple[ProviderMetadata, ...]:
        """Return provider metadata without exposing internal mutable state."""
        providers = tuple(self._providers.values())
        if enabled_only:
            return tuple(provider for provider in providers if provider.enabled)
        return providers

    def list_models(
        self,
        *,
        provider: str | None = None,
        enabled_only: bool = False,
    ) -> tuple[ModelMetadata, ...]:
        """Return model metadata filtered only by infrastructure state."""
        models = tuple(self._models.values())
        if provider is not None:
            models = tuple(model for model in models if model.provider_id == provider)
        if enabled_only:
            models = tuple(model for model in models if model.enabled)
        return models
