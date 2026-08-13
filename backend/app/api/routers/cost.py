"""Cost estimation and comparison endpoints backed by the model registry."""

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import current_user
from app.models.user import User
from app.api.schemas import (
    BudgetStatusResponse,
    CostCompareRequest,
    CostCompareResponse,
    CostEstimateResponse,
    CostRequest,
    CostSavingsRecommendationResponse,
)
from app.cost import CostComparator, CostEstimate, CostEstimator
from app.models_registry import model_registry


router = APIRouter(prefix="/cost", tags=["cost"])
_estimator = CostEstimator()
_comparator = CostComparator()


def _estimate(request: CostRequest, ignore_disabled: bool = False) -> CostEstimate:
    try:
        model = model_registry.get_model(request.provider_id, request.model_id)
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown model '{request.provider_id}/{request.model_id}'",
        ) from error
    if not model.enabled and not ignore_disabled:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Model is disabled")
    return _estimator.estimate_with_token_prices(
        model.provider_id, model.model_id, request.input_tokens, request.output_tokens,
        model.cost_per_1k_input_tokens, model.cost_per_1k_output_tokens,
    )


def _response(estimate: CostEstimate) -> CostEstimateResponse:
    return CostEstimateResponse(
        provider_id=estimate.provider,
        model_id=estimate.model,
        input_tokens=estimate.input_tokens,
        output_tokens=estimate.output_tokens,
        estimated_cost_usd=estimate.estimated_cost,
        daily_forecast_usd=estimate.daily_forecast_usd,
        monthly_forecast_usd=estimate.monthly_forecast_usd,
    )


@router.post("/estimate", response_model=CostEstimateResponse, summary="Estimate model cost")
async def estimate_cost(request: CostRequest, user: User = Depends(current_user)) -> CostEstimateResponse:
    """Estimate USD cost from registry pricing and supplied input/output token counts."""
    return _response(_estimate(request))


@router.post("/compare", response_model=CostCompareResponse, summary="Compare model costs")
async def compare_costs(request: CostCompareRequest, user: User = Depends(current_user)) -> CostCompareResponse:
    """Compare selected models, or every enabled catalog model when none are supplied."""
    report = _comparator.compare_all(request.input_tokens, request.output_tokens)
    
    estimates_list = [
        CostEstimateResponse(
            provider_id=c.provider_id,
            model_id=c.model_id,
            input_tokens=request.input_tokens,
            output_tokens=request.output_tokens,
            estimated_cost_usd=Decimal(str(c.cost_estimate.total_cost_usd)),
            daily_forecast_usd=Decimal(str(c.cost_estimate.total_cost_usd)) * Decimal("1000"),
            monthly_forecast_usd=Decimal(str(c.cost_estimate.total_cost_usd)) * Decimal("30000"),
        )
        for c in report.comparisons
    ]
    cheapest_item = report.comparisons[0]
    most_expensive_item = report.comparisons[-1]

    cheapest_resp = CostEstimateResponse(
        provider_id=cheapest_item.provider_id,
        model_id=cheapest_item.model_id,
        input_tokens=request.input_tokens,
        output_tokens=request.output_tokens,
        estimated_cost_usd=Decimal(str(cheapest_item.cost_estimate.total_cost_usd)),
        daily_forecast_usd=Decimal(str(cheapest_item.cost_estimate.total_cost_usd)) * Decimal("1000"),
        monthly_forecast_usd=Decimal(str(cheapest_item.cost_estimate.total_cost_usd)) * Decimal("30000"),
    )

    most_expensive_resp = CostEstimateResponse(
        provider_id=most_expensive_item.provider_id,
        model_id=most_expensive_item.model_id,
        input_tokens=request.input_tokens,
        output_tokens=request.output_tokens,
        estimated_cost_usd=Decimal(str(most_expensive_item.cost_estimate.total_cost_usd)),
        daily_forecast_usd=Decimal(str(most_expensive_item.cost_estimate.total_cost_usd)) * Decimal("1000"),
        monthly_forecast_usd=Decimal(str(most_expensive_item.cost_estimate.total_cost_usd)) * Decimal("30000"),
    )

    return CostCompareResponse(
        estimates=estimates_list,
        cheapest=cheapest_resp,
        most_expensive=most_expensive_resp,
        savings_amount_usd=Decimal(str(report.max_savings_usd)),
        savings_percentage=Decimal(str(report.max_savings_pct)),
        recommendations=[],
    )


@router.get("/budget", response_model=BudgetStatusResponse, summary="Get workspace budget status")
async def get_budget(
    workspace_id: str = Query(default="default"),
    monthly_budget_usd: Decimal = Query(default=Decimal("500.00")),
    current_spend_usd: Decimal = Query(default=Decimal("124.50")),
    user: User = Depends(current_user),
) -> BudgetStatusResponse:
    """Check workspace budget limits, current spend, and threshold warnings."""
    pct = (current_spend_usd / monthly_budget_usd * 100) if monthly_budget_usd > 0 else Decimal("0")
    warn = "normal"
    if pct >= 100:
        warn = "exceeded"
    elif pct >= 90:
        warn = "warning_90"
    elif pct >= 80:
        warn = "warning_80"

    return BudgetStatusResponse(
        workspace_id=workspace_id,
        monthly_budget_usd=monthly_budget_usd,
        current_spend_usd=current_spend_usd,
        percentage_used=round(pct, 1),
        warning_status=warn,
        hard_stop_triggered=warn == "exceeded",
    )


@router.get("/recommendations", response_model=list[CostSavingsRecommendationResponse], summary="Get cost optimization suggestions")
async def get_recommendations(user: User = Depends(current_user)) -> list[CostSavingsRecommendationResponse]:
    """Return automated AI model cost optimization recommendations across catalog."""
    report = cost_optimization_engine.generate_recommendations(
        prompt="Write a function to process user requests",
        selected_provider="openai",
        selected_model="gpt-4o",
        prompt_tokens=250,
    )
    return [
        CostSavingsRecommendationResponse(
            current_model="openai/gpt-4o",
            recommended_model="gemini/gemini-2.0-flash",
            savings_percentage=r.potential_savings_pct,
            savings_amount_usd=0.015,
            suggestion_text=f"{r.title}: {r.description} ({r.recommended_action})",
        )
        for r in report.recommendations
    ]


from pydantic import BaseModel, Field
from app.cost import cost_optimization_engine


class OptimizationRequest(BaseModel):
    prompt: str = Field(min_length=1)
    selected_provider: str = Field(default="openai")
    selected_model: str = Field(default="gpt-4o")
    prompt_tokens: int = Field(ge=1, default=500)
    conversation_turns: int = Field(ge=1, default=1)


@router.post("/optimize", summary="Generate cost optimization recommendations")
async def generate_cost_optimizations(request: OptimizationRequest, user: User = Depends(current_user)):
    """Generate rule-based cost optimization recommendations."""
    report = cost_optimization_engine.generate_recommendations(
        prompt=request.prompt,
        selected_provider=request.selected_provider,
        selected_model=request.selected_model,
        prompt_tokens=request.prompt_tokens,
        conversation_turns=request.conversation_turns,
    )
    return report.to_dict()
