from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas import (
    CandidateScoreResponse,
    RouteRequest,
    RouteResponse,
    RoutingExplanationResponse,
)
from app.cost import CostCalculator
from app.models_registry import model_registry
from app.providers.manager import provider_manager
from app.routing import (
    BalancedStrategy,
    CheapestStrategy,
    CustomWeightedStrategy,
    EmbeddingOptimizedStrategy,
    FastestStrategy,
    HighestQualityStrategy,
    ImageGenerationOptimizedStrategy,
    IntelligentRouter,
    ModelInfo,
    ReasoningOptimizedStrategy,
    TaskCategory,
    VisionOptimizedStrategy,
)

router = APIRouter(prefix="/routing", tags=["routing"])

_STRATEGIES = {
    "balanced": BalancedStrategy,
    "cheapest": CheapestStrategy,
    "fastest": FastestStrategy,
    "highest_quality": HighestQualityStrategy,
    "reasoning_optimized": ReasoningOptimizedStrategy,
    "vision_optimized": VisionOptimizedStrategy,
    "embedding_optimized": EmbeddingOptimizedStrategy,
    "image_generation_optimized": ImageGenerationOptimizedStrategy,
}


def _get_strategy(name: str, weights: dict[str, float] | None = None):
    if name == "custom_weighted":
        w = weights or {}
        return CustomWeightedStrategy(
            cost_weight=w.get("cost", 0.25),
            latency_weight=w.get("latency", 0.25),
            quality_weight=w.get("quality", 0.25),
            reasoning_weight=w.get("reasoning", 0.25),
        )
    return _STRATEGIES.get(name, BalancedStrategy)()


def _build_candidates(provider_ids: set[str] | None = None) -> list[ModelInfo]:
    enabled_providers = {
        p_name for p_name in provider_manager.provider_names()
        if provider_manager.get_config(p_name).get("enabled", False)
        and provider_manager.get_config(p_name).get("status") in ("healthy", "configured")
    }
    p_ids = provider_ids or (enabled_providers if enabled_providers else {m.provider_id for m in model_registry.list_models()})
    configs = {c["provider_id"]: c for c in provider_manager.list_configs()}

    candidates = []
    for model in model_registry.list_models(enabled_only=True):
        if model.provider_id not in p_ids:
            continue
        cfg = configs.get(model.provider_id, {})
        if cfg and (not cfg.get("enabled", False) or cfg.get("status") in ("disabled", "unconfigured")):
            continue
        status_val = cfg.get("status", "healthy")
        failures = cfg.get("consecutive_failures", 0)

        candidates.append(
            ModelInfo(
                provider=model.provider_id,
                model_name=model.model_id,
                cost_per_1k_tokens=float(
                    model.cost_per_1k_input_tokens + model.cost_per_1k_output_tokens
                ),
                latency=float(model.average_latency_ms),
                capabilities=frozenset(
                    TaskCategory(capability)
                    for capability in model.capabilities
                    if capability in TaskCategory._value2member_map_
                ),
                priority=model.priority,
                category=model.category,
                context_window=model.context_window,
                max_output_tokens=model.max_output_tokens,
                quality_score=model.quality_score,
                reasoning_score=model.reasoning_score,
                speed_score=model.speed_score,
                provider_status=status_val,
                provider_failures=failures,
                supports_streaming=model.supports_streaming,
                supports_vision=model.supports_vision,
                supports_audio=model.supports_audio,
                supports_function_calling=model.supports_function_calling,
            )
        )
    return candidates


@router.post("/route", response_model=RouteResponse, summary="Select a model")
async def route_model(request: RouteRequest) -> RouteResponse:
    """Choose a compatible enabled model using the requested routing strategy and provider health monitoring."""
    candidates = _build_candidates(set(request.provider_ids) if request.provider_ids else None)
    strategy = _get_strategy(request.strategy, request.weights)
    router_inst = IntelligentRouter(strategy=strategy)

    try:
        explanation = router_inst.evaluate_with_explanation(
            request.task_category, candidates, strategy_name=request.strategy
        )
        metadata = model_registry.get_model(
            explanation.selected_provider, explanation.selected_model
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error

    # Compute estimated request cost if tokens provided
    calc = CostCalculator()
    est_cost = calc.calculate_token_costs(
        request.prompt_tokens,
        request.max_completion_tokens,
        metadata.cost_per_1k_input_tokens,
        metadata.cost_per_1k_output_tokens,
    )

    explanation_resp = RoutingExplanationResponse(
        selected_provider_id=explanation.selected_provider,
        selected_model_id=explanation.selected_model,
        strategy=explanation.strategy_used,
        primary_reason=explanation.primary_reason,
        ranked_candidates=[
            CandidateScoreResponse(
                provider_id=c.provider,
                model_id=c.model_name,
                overall_score=c.overall_score,
                rank=c.rank,
                cost_per_1k_tokens=Decimal(str(c.cost_per_1k_tokens)),
                latency_ms=int(c.latency),
                quality_score=c.quality_score,
                reasoning_score=c.reasoning_score,
                status=c.status,
                reason=c.reason,
            )
            for c in explanation.ranked_candidates
        ],
        failover_triggered=explanation.failover_triggered,
        circuit_breaker_bypassed=list(explanation.circuit_breaker_bypassed),
    )

    return RouteResponse(
        provider_id=metadata.provider_id,
        model_id=metadata.model_id,
        task_category=request.task_category,
        strategy=request.strategy,
        estimated_latency_ms=metadata.average_latency_ms,
        cost_per_1k_input_tokens=metadata.cost_per_1k_input_tokens,
        cost_per_1k_output_tokens=metadata.cost_per_1k_output_tokens,
        estimated_cost_usd=est_cost,
        failover_triggered=explanation.failover_triggered,
        circuit_breaker_bypassed=list(explanation.circuit_breaker_bypassed),
        explanation=explanation_resp,
    )


@router.post(
    "/explain",
    response_model=RoutingExplanationResponse,
    summary="Explain routing decision",
)
async def explain_route(request: RouteRequest) -> RoutingExplanationResponse:
    """Return transparent candidate ranking, scores, and decision explanation without executing model invocation."""
    candidates = _build_candidates(set(request.provider_ids) if request.provider_ids else None)
    strategy = _get_strategy(request.strategy, request.weights)
    router_inst = IntelligentRouter(strategy=strategy)

    try:
        explanation = router_inst.evaluate_with_explanation(
            request.task_category, candidates, strategy_name=request.strategy
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error

    return RoutingExplanationResponse(
        selected_provider_id=explanation.selected_provider,
        selected_model_id=explanation.selected_model,
        strategy=explanation.strategy_used,
        primary_reason=explanation.primary_reason,
        ranked_candidates=[
            CandidateScoreResponse(
                provider_id=c.provider,
                model_id=c.model_name,
                overall_score=c.overall_score,
                rank=c.rank,
                cost_per_1k_tokens=Decimal(str(c.cost_per_1k_tokens)),
                latency_ms=int(c.latency),
                quality_score=c.quality_score,
                reasoning_score=c.reasoning_score,
                status=c.status,
                reason=c.reason,
            )
            for c in explanation.ranked_candidates
        ],
        failover_triggered=explanation.failover_triggered,
        circuit_breaker_bypassed=list(explanation.circuit_breaker_bypassed),
    )


from pydantic import BaseModel, Field
from app.api.dependencies import current_user
from app.models.user import User
from app.orchestration.capabilities import capability_engine
from app.orchestration.intent import intent_detector
from app.orchestration.router import adaptive_router


class IntentRequest(BaseModel):
    prompt: str = Field(min_length=1)
    system_prompt: str = ""
    has_attachments: bool = False


class AdaptiveRouteRequest(BaseModel):
    prompt: str = Field(min_length=1)
    system_prompt: str = ""
    has_attachments: bool = False
    strategy_override: str | None = None
    workspace_id: str = "default"


@router.post("/intent", summary="Detect request intent and profile workload")
async def detect_intent(request: IntentRequest, user: User = Depends(current_user)):
    """Detect intent category, confidence, required capabilities, and profile workload."""
    intent_res = intent_detector.detect_intent(prompt=request.prompt, has_attachments=request.has_attachments)
    profile = intent_detector.profile_request(prompt=request.prompt, system_prompt=request.system_prompt, has_attachments=request.has_attachments)
    return {
        "intent": intent_res.to_dict(),
        "profile": profile.to_dict(),
    }


@router.post("/adaptive", summary="Perform adaptive smart model selection")
async def perform_adaptive_routing(request: AdaptiveRouteRequest, user: User = Depends(current_user)):
    """Execute adaptive routing and return explainable model decision."""
    result = adaptive_router.route(
        prompt=request.prompt,
        system_prompt=request.system_prompt,
        has_attachments=request.has_attachments,
        strategy_override=request.strategy_override,
        user_id=user.id,
        workspace_id=request.workspace_id,
    )
    return result.to_dict()


@router.get("/capabilities", summary="List model capabilities catalog")
async def list_model_capabilities(user: User = Depends(current_user)):
    """Retrieve capability profiles for all registered catalog models."""
    caps = capability_engine.list_capabilities()
    return [c.to_dict() for c in caps]


@router.get("/strategies", summary="List available routing strategies")
async def list_routing_strategies(user: User = Depends(current_user)):
    """Retrieve supported routing strategies and descriptions."""
    return [
        {
            "id": "ADAPTIVE_SMART",
            "name": "Adaptive Smart Orchestrator",
            "description": "Automatically profiles prompt intent, required capabilities, and provider health to select optimal model.",
        },
        {
            "id": "COST_MINIMIZER",
            "name": "Cost Minimizer",
            "description": "Prioritizes model cost efficiency while satisfying minimum capability thresholds.",
        },
        {
            "id": "LATENCY_OPTIMIZED",
            "name": "Latency Optimized",
            "description": "Prioritizes lowest response time and P95 latency.",
        },
        {
            "id": "QUALITY_MAXIMIZER",
            "name": "Quality & Reasoning Maximizer",
            "description": "Selects frontier reasoning models for complex coding, math, and logic tasks.",
        },
        {
            "id": "FALLBACK_RELIABILITY",
            "name": "Fallback Reliability Chain",
            "description": "Routes through fallback hierarchy to ensure 99.99% request completion.",
        },
    ]
