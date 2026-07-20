"""Provider and model catalog endpoints."""

from fastapi import APIRouter, Query

from app.api.schemas import ModelResponse, ProviderResponse
from app.models_registry import model_registry
from app.providers.manager import provider_manager


router = APIRouter(tags=["catalog"])


@router.get("/providers", response_model=list[ProviderResponse], summary="List providers")
async def list_providers() -> list[ProviderResponse]:
    """Return catalog providers and local adapter configuration status."""
    checks = {report["provider"]: report for report in await provider_manager.health_checks()}
    registered = set(provider_manager.provider_names())
    return [
        ProviderResponse(
            provider_id=provider.provider_id,
            provider_name=provider.provider_name,
            enabled=provider.enabled,
            adapter_registered=provider.provider_id in registered,
            status=checks.get(provider.provider_id, {}).get("status"),
            configured_model=checks.get(provider.provider_id, {}).get("model"),
        )
        for provider in model_registry.list_providers()
    ]


@router.get("/models", response_model=list[ModelResponse], summary="List models")
async def list_models(
    provider_id: str | None = Query(default=None),
    enabled_only: bool = Query(default=False),
) -> list[ModelResponse]:
    """Return registry models, optionally filtered by provider and enabled state."""
    return [
        ModelResponse(
            provider_id=model.provider_id,
            provider_name=model.provider_name,
            model_id=model.model_id,
            display_name=model.display_name,
            capabilities=sorted(model.capabilities),
            cost_per_1k_input_tokens=model.cost_per_1k_input_tokens,
            cost_per_1k_output_tokens=model.cost_per_1k_output_tokens,
            average_latency_ms=model.average_latency_ms,
            priority=model.priority,
            context_window=model.context_window,
            enabled=model.enabled,
        )
        for model in model_registry.list_models(
            provider=provider_id,
            enabled_only=enabled_only,
        )
    ]
