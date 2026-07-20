"""Catalog loading boundary for replaceable model metadata sources."""

from collections.abc import Iterable

from app.models_registry.catalog.default_catalog import DEFAULT_MODELS, DEFAULT_PROVIDERS
from app.models_registry.registry import ModelRegistry
from app.models_registry.schemas import ModelMetadata, ProviderMetadata


def build_model_registry(
    providers: Iterable[ProviderMetadata] = DEFAULT_PROVIDERS,
    models: Iterable[ModelMetadata] = DEFAULT_MODELS,
) -> ModelRegistry:
    """Build a registry from metadata that a database or admin source can later replace."""
    return ModelRegistry(providers=providers, models=models)


# Loading the default catalog at import time makes populated read-only metadata
# available during normal application startup without coupling it to the API layer.
model_registry = build_model_registry()


__all__ = ["DEFAULT_MODELS", "DEFAULT_PROVIDERS", "build_model_registry", "model_registry"]
