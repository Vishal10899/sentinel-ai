"""Metadata-only model routing endpoint."""

from fastapi import APIRouter, HTTPException, status

from app.api.schemas import RouteRequest, RouteResponse
from app.models_registry import model_registry
from app.providers.manager import provider_manager
from app.routing import BalancedStrategy, CheapestStrategy, FastestStrategy, IntelligentRouter, ModelInfo


router = APIRouter(prefix="/routing", tags=["routing"])

_STRATEGIES = {
    "balanced": BalancedStrategy,
    "cheapest": CheapestStrategy,
    "fastest": FastestStrategy,
}


@router.post("/route", response_model=RouteResponse, summary="Select a model")
async def route_model(request: RouteRequest) -> RouteResponse:
    """Choose a compatible enabled model using the requested routing strategy."""
    provider_ids = set(request.provider_ids or provider_manager.provider_names())
    candidates = [
        ModelInfo(
            provider=model.provider_id,
            model_name=model.model_id,
            cost_per_1k_tokens=float(
                model.cost_per_1k_input_tokens + model.cost_per_1k_output_tokens
            ),
            latency=float(model.average_latency_ms),
            capabilities=frozenset(request.task_category.__class__(capability) for capability in model.capabilities),
            priority=model.priority,
        )
        for model in model_registry.list_models(enabled_only=True)
        if model.provider_id in provider_ids
    ]
    try:
        selected = IntelligentRouter(strategy=_STRATEGIES[request.strategy]()).select_model(
            request.task_category, candidates
        )
        metadata = model_registry.get_model(selected.provider, selected.model_name)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error

    return RouteResponse(
        provider_id=metadata.provider_id,
        model_id=metadata.model_id,
        task_category=request.task_category,
        strategy=request.strategy,
        estimated_latency_ms=metadata.average_latency_ms,
        cost_per_1k_input_tokens=metadata.cost_per_1k_input_tokens,
        cost_per_1k_output_tokens=metadata.cost_per_1k_output_tokens,
    )
