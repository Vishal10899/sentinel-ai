"""Cost estimation and comparison endpoints backed by the model registry."""

from fastapi import APIRouter, HTTPException, status

from app.api.schemas import CostCompareRequest, CostCompareResponse, CostEstimateResponse, CostRequest
from app.cost import CostComparator, CostEstimate, CostEstimator
from app.models_registry import model_registry


router = APIRouter(prefix="/cost", tags=["cost"])
_estimator = CostEstimator()
_comparator = CostComparator()


def _estimate(request: CostRequest) -> CostEstimate:
    try:
        model = model_registry.get_model(request.provider_id, request.model_id)
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown model '{request.provider_id}/{request.model_id}'",
        ) from error
    if not model.enabled:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Model is disabled")
    return _estimator.estimate_with_token_prices(
        model.provider_id, model.model_id, request.input_tokens, request.output_tokens,
        model.cost_per_1k_input_tokens, model.cost_per_1k_output_tokens,
    )


def _response(estimate: CostEstimate) -> CostEstimateResponse:
    return CostEstimateResponse(
        provider_id=estimate.provider, model_id=estimate.model,
        input_tokens=estimate.input_tokens, output_tokens=estimate.output_tokens,
        estimated_cost_usd=estimate.estimated_cost,
    )


@router.post("/estimate", response_model=CostEstimateResponse, summary="Estimate model cost")
async def estimate_cost(request: CostRequest) -> CostEstimateResponse:
    """Estimate USD cost from registry pricing and supplied input/output token counts."""
    return _response(_estimate(request))


@router.post("/compare", response_model=CostCompareResponse, summary="Compare model costs")
async def compare_costs(request: CostCompareRequest) -> CostCompareResponse:
    """Compare selected models, or every enabled catalog model when none are supplied."""
    selections = request.models or [
        CostRequest(
            provider_id=model.provider_id, model_id=model.model_id,
            input_tokens=request.input_tokens, output_tokens=request.output_tokens,
        )
        for model in model_registry.list_models(enabled_only=True)
    ]
    if request.models:
        selections = [
            CostRequest(
                provider_id=model.provider_id,
                model_id=model.model_id,
                input_tokens=request.input_tokens,
                output_tokens=request.output_tokens,
            )
            for model in request.models
        ]
    estimates = [_estimate(selection) for selection in selections]
    comparison = _comparator.compare(estimates)
    return CostCompareResponse(
        estimates=[_response(estimate) for estimate in estimates],
        cheapest=_response(comparison.cheapest),
        most_expensive=_response(comparison.most_expensive),
        savings_amount_usd=comparison.savings_amount,
        savings_percentage=comparison.savings_percentage,
    )
