"""Public read-only model registry infrastructure."""

from app.models_registry.catalog import build_model_registry, model_registry
from app.models_registry.registry import ModelRegistry
from app.models_registry.schemas import ModelMetadata, ProviderMetadata

__all__ = [
    "ModelMetadata",
    "ModelRegistry",
    "ProviderMetadata",
    "build_model_registry",
    "model_registry",
]
