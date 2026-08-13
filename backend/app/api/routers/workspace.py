"""Protected MVP workspace endpoints: execution, history, analytics, provider setup."""
from dataclasses import asdict
from time import perf_counter
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.dependencies import current_user
from app.api.schemas import PlaygroundRequest, ProviderConfigRequest
from app.models.user import User
from app.cost import CostEstimator
from app.history.store import history_store
from app.models_registry import model_registry
from app.providers.manager import provider_manager
from app.routing import BalancedStrategy, CheapestStrategy, FastestStrategy, IntelligentRouter, ModelInfo

router=APIRouter(tags=["workspace"])
_strategies={"balanced":BalancedStrategy,"cheapest":CheapestStrategy,"fastest":FastestStrategy}

@router.post("/playground/execute")
async def execute(
    request: PlaygroundRequest,
    user: User = Depends(current_user),
) -> dict[str, object]:

    available = []
    provider_status = {
        name: (await provider_manager.get(name).health()).get("status") == "configured"
        for name in provider_manager.provider_names()
    }

    for model in model_registry.list_models(enabled_only=True):
        if not provider_status.get(model.provider_id):
            continue

        available.append(
            ModelInfo(
                model.provider_id,
                model.model_id,
                float(
                    model.cost_per_1k_input_tokens
                    + model.cost_per_1k_output_tokens
                ),
                float(model.average_latency_ms),
                frozenset(
                    request.task_category.__class__(cap)
                    for cap in model.capabilities
                ),
                model.priority,
            )
        )

    try:
        selected = IntelligentRouter(
            _strategies[request.strategy]()
        ).select_model(
            request.task_category,
            available,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    metadata = model_registry.get_model(
        selected.provider,
        selected.model_name,
    )

    estimate = CostEstimator().estimate_with_token_prices(
        metadata.provider_id,
        metadata.model_id,
        request.input_tokens,
        request.output_tokens,
        metadata.cost_per_1k_input_tokens,
        metadata.cost_per_1k_output_tokens,
    )

    started = perf_counter()

    try:
        response = await provider_manager.get(
      selected.provider
        ).generate(
            request.prompt,
          model=selected.model_name,
          output_tokens=request.output_tokens,
        )
    except (NotImplementedError, RuntimeError) as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    item = history_store.add(
        user.id,
        prompt=request.prompt,
        provider_id=selected.provider,
        model_id=selected.model_name,
        response=response,
        estimated_cost_usd=str(estimate.estimated_cost),
        latency_ms=round((perf_counter() - started) * 1000),
    )

    return {
        **asdict(item),
        "capabilities": sorted(metadata.capabilities),
        "reason": f"{request.strategy.title()} strategy selected this compatible model.",
    }


@router.get("/history")
async def history(
    query: str = "",
    user: User = Depends(current_user),
) -> list[dict[str, object]]:
    return history_store.list(user.id, query)


@router.get("/analytics")
async def analytics(
    user: User = Depends(current_user),
) -> dict[str, object]:
    items = history_store.list(user.id)
    total_cost = sum(float(item["estimated_cost_usd"]) for item in items)
    providers: dict[str, int] = {}
    for item in items:
        provider_id = item["provider_id"]
        providers[provider_id] = providers.get(provider_id, 0) + 1

    total_requests = len(items)

    try:
        from app.db.session import get_db_session
        from app.repositories.workspace_repository import WorkspaceRepository
        from app.repositories.conversation_repository import ConversationRepository
        from app.repositories.message_repository import MessageRepository

        async with get_db_session() as db:
            workspace = await WorkspaceRepository(db).get_by_owner(user.id)
            if workspace:
                convs = await ConversationRepository(db).list_by_workspace(str(workspace.id))
                for conv in convs:
                    msgs = await MessageRepository(db).list_by_conversation(str(conv.id))
                    for m in msgs:
                        if m.role == "assistant":
                            total_requests += 1
                            total_cost += float(m.cost or 0.0)
                            p = m.provider or "gemini"
                            providers[p] = providers.get(p, 0) + 1
    except Exception:
        pass

    return {
        "total_requests": total_requests,
        "estimated_cost_usd": round(total_cost, 6),
        "money_saved_usd": round(total_cost * 0.3, 4),
        "provider_usage": [
            {"provider": provider_id, "requests": requests}
            for provider_id, requests in providers.items()
        ] if providers else [{"provider": "gemini", "requests": total_requests}],
        "recent_activity": items[:10],
    }


@router.put("/providers/{provider_id}/configuration", operation_id="configure_workspace_provider")
async def configure_workspace_provider(
    provider_id: str,
    request: ProviderConfigRequest,
    _: User = Depends(current_user),
) -> dict[str, str]:
    try:
        provider_manager.configure(
            provider_id,
            api_key=request.api_key,
            model=request.model,
            enabled=request.enabled,
        )
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Provider adapter not available",
        ) from error
    return await provider_manager.get(provider_id).health()


@router.post("/providers/{provider_id}/test", operation_id="test_workspace_provider")
async def test_workspace_provider(
    provider_id: str,
    _: User = Depends(current_user),
) -> dict[str, str]:
    try:
        return await provider_manager.get(provider_id).health()
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Provider adapter not available",
        ) from error


@router.get("/routing/learning-stats")
async def get_routing_learning_stats(
    _: User = Depends(current_user),
) -> dict[str, object]:
    """Return aggregated execution metadata and continuous learning statistics."""
    from app.routing.learning import continuous_learning_engine
    return continuous_learning_engine.get_telemetry_summary()
