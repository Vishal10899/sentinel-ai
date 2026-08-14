from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.api.schemas import (
    ModelResponse,
    ProviderCreateRequest,
    ProviderConfigRequest,
    ProviderFailoverRequest,
    ProviderResponse,
    ProviderTestResponse,
)
from app.models_registry import model_registry
from app.providers.manager import provider_manager
from app.providers.security import mask_api_key, sanitize_base_url
from app.repositories import ProviderRepository


router = APIRouter(tags=["catalog"])


async def _flush_caches():
    """Flush Redis cache database and local semantic cache."""
    try:
        from app.cache.client import get_redis
        client = await get_redis()
        if client:
            await client.flushdb()
    except Exception:
        pass
    try:
        from app.cache import semantic_cache
        semantic_cache.clear()
    except Exception:
        pass


def _build_provider_response(cfg: dict) -> ProviderResponse:
    registered = set(provider_manager.provider_names())
    pid = cfg["provider_id"]
    return ProviderResponse(
        provider_id=pid,
        provider_name=cfg.get("provider_name", pid.capitalize()),
        enabled=cfg.get("enabled", True),
        adapter_registered=pid in registered,
        status=cfg.get("status", "unconfigured"),
        configured_model=cfg.get("default_model"),
        api_key_masked=mask_api_key(cfg.get("api_key")),
        base_url=cfg.get("base_url"),
        organization_id=cfg.get("organization_id"),
        timeout_seconds=cfg.get("timeout_seconds", 30),
        retry_count=cfg.get("retry_count", 3),
        rate_limit_rpm=cfg.get("rate_limit_rpm", 600),
        rate_limit_tpm=cfg.get("rate_limit_tpm", 100000),
        priority=cfg.get("priority", 10),
        cost_multiplier=cfg.get("cost_multiplier", 1.0),
        primary_provider_id=cfg.get("primary_provider_id"),
        secondary_provider_id=cfg.get("secondary_provider_id"),
        auto_failover=cfg.get("auto_failover", True),
        supports_streaming=cfg.get("supports_streaming", True),
        supports_vision=cfg.get("supports_vision", False),
        supports_audio=cfg.get("supports_audio", False),
        supports_function_calling=cfg.get("supports_function_calling", True),
        supports_embeddings=cfg.get("supports_embeddings", True),
        supports_image_generation=cfg.get("supports_image_generation", False),
        supports_moderation=cfg.get("supports_moderation", False),
        last_latency_ms=cfg.get("last_latency_ms", 0),
        last_health_check=cfg.get("last_health_check"),
        last_failure=cfg.get("last_failure"),
        failure_count=cfg.get("failure_count", 0),
        consecutive_failures=cfg.get("consecutive_failures", 0),
    )


@router.get("/providers", response_model=list[ProviderResponse], summary="List providers")
async def list_providers(user: User = Depends(require_permission("provider.manage"))) -> list[ProviderResponse]:
    """Return catalog providers and local adapter configuration status."""
    configs = provider_manager.list_configs()
    if not configs:
        # Fallback to catalog providers
        return [
            ProviderResponse(
                provider_id=p.provider_id,
                provider_name=p.provider_name,
                enabled=p.enabled,
                adapter_registered=p.provider_id in provider_manager.provider_names(),
                status="configured" if p.enabled else "disabled",
            )
            for p in model_registry.list_providers()
        ]
    return [_build_provider_response(cfg) for cfg in configs]


@router.get("/providers/{provider_id}", response_model=ProviderResponse, summary="Get provider details")
async def get_provider_detail(provider_id: str, user: User = Depends(current_user)) -> ProviderResponse:
    """Return enterprise configuration and live metrics for a single provider."""
    try:
        cfg = provider_manager.get_config(provider_id)
        return _build_provider_response(cfg)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' not found",
        )


@router.post("/providers", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED, summary="Create provider")
async def create_provider(
    request: ProviderCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("provider.manage")),
) -> ProviderResponse:
    """Create a new custom provider configuration."""
    if request.provider_id in provider_manager.provider_names():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Provider '{request.provider_id}' already exists",
        )
    from app.providers.anthropic_provider import AnthropicProvider
    custom_cls = type(
        f"CustomProvider_{request.provider_id}",
        (AnthropicProvider,),
        {"name": property(lambda self: getattr(self, "_name", request.provider_id))},
    )
    adapter = custom_cls(api_key=request.api_key, model=request.default_model or "default")
    adapter._name = request.provider_id

    provider_manager.register(adapter)
    payload = request.model_dump()
    if "base_url" in payload:
        payload["base_url"] = sanitize_base_url(payload["base_url"], None)

    provider_manager.configure(request.provider_id, **payload)
    cfg = provider_manager.get_config(request.provider_id)

    try:
        repo = ProviderRepository(db)
        await repo.save_or_update(request.provider_id, cfg)
    except Exception as db_err:
        print(f"[Warning] Failed to persist new provider to DB: {db_err}", flush=True)

    await _flush_caches()
    return _build_provider_response(cfg)


@router.put("/providers/{provider_id}", response_model=ProviderResponse, summary="Configure provider")
@router.put("/providers/{provider_id}/configuration", response_model=ProviderResponse, summary="Configure provider")
async def configure_provider(
    provider_id: str,
    request: ProviderConfigRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("provider.manage")),
) -> ProviderResponse:

    """Update runtime settings, limits, features, or credentials for a provider."""
    try:
        payload = request.model_dump(exclude_unset=True)
        default_endpoints = {
            "gemini": "https://generativelanguage.googleapis.com",
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com",
            "ollama": "http://127.0.0.1:11434",
        }
        default_url = default_endpoints.get(provider_id)
        if "base_url" in payload:
            payload["base_url"] = sanitize_base_url(payload["base_url"], default_url)
        if "model" in payload and payload["model"]:
            payload["default_model"] = payload["model"]

        provider_manager.configure(provider_id, **payload)
        cfg = provider_manager.get_config(provider_id)

        # DB Persistence
        try:
            repo = ProviderRepository(db)
            await repo.save_or_update(provider_id, cfg)
        except Exception as db_err:
            print(f"[Warning] Failed to persist provider config to DB: {db_err}", flush=True)

        # Cache Invalidation / Flush
        await _flush_caches()

        return _build_provider_response(cfg)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' not found",
        )


@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete provider")
async def delete_provider(provider_id: str, user: User = Depends(require_permission("provider.manage"))) -> None:
    """Remove a provider configuration."""
    if provider_id not in provider_manager.provider_names():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' not found",
        )
    provider_manager.unregister(provider_id)
    await _flush_caches()


@router.post("/providers/{provider_id}/test", response_model=ProviderTestResponse, summary="Test provider connection")
async def test_provider(provider_id: str, user: User = Depends(current_user)) -> ProviderTestResponse:
    """Execute live connection and credential validation test."""
    try:
        res = await provider_manager.test_connection(provider_id)
        return ProviderTestResponse(
            provider_id=provider_id,
            valid=res.get("valid", False),
            status=res.get("status", "unhealthy"),
            message=res.get("message", "Test completed"),
            latency_ms=res.get("latency_ms", 0),
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' not found",
        )


@router.post("/providers/{provider_id}/health-check", response_model=ProviderResponse, summary="Run health check")
async def health_check_provider(provider_id: str, user: User = Depends(current_user)) -> ProviderResponse:
    """Perform live health check and update metrics."""
    try:
        await provider_manager.test_connection(provider_id)
        cfg = provider_manager.get_config(provider_id)
        return _build_provider_response(cfg)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' not found",
        )


@router.put("/providers/{provider_id}/failover", response_model=ProviderResponse, summary="Configure provider failover")
async def update_failover(
    provider_id: str,
    request: ProviderFailoverRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("provider.manage")),
) -> ProviderResponse:
    """Configure primary/secondary failover targets for automatic resilience."""
    try:
        payload = request.model_dump(exclude_unset=True)
        provider_manager.configure(provider_id, **payload)
        cfg = provider_manager.get_config(provider_id)

        try:
            repo = ProviderRepository(db)
            await repo.save_or_update(provider_id, cfg)
        except Exception as db_err:
            print(f"[Warning] Failed to persist failover update to DB: {db_err}", flush=True)

        await _flush_caches()
        return _build_provider_response(cfg)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' not found",
        )


@router.post("/providers/{provider_id}/toggle", response_model=ProviderResponse, summary="Toggle provider enabled state")
async def toggle_provider(
    provider_id: str,
    enabled: bool = Query(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("provider.manage")),
) -> ProviderResponse:

    """Enable or disable a provider."""
    try:
        provider_manager.configure(provider_id, enabled=enabled)
        cfg = provider_manager.get_config(provider_id)

        try:
            repo = ProviderRepository(db)
            await repo.save_or_update(provider_id, cfg)
        except Exception as db_err:
            print(f"[Warning] Failed to persist provider toggle to DB: {db_err}", flush=True)

        await _flush_caches()
        return _build_provider_response(cfg)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' not found",
        )



@router.get("/models", response_model=list[ModelResponse], summary="List models")
async def list_models(
    provider_id: str | None = Query(default=None),
    category: str | None = Query(default=None),
    enabled_only: bool = Query(default=False),
    user: User = Depends(require_permission("view_models")),
) -> list[ModelResponse]:
    """Return registry models, optionally filtered by provider, category, and enabled state."""
    return [
        ModelResponse(
            provider_id=model.provider_id,
            provider_name=model.provider_name,
            model_id=model.model_id,
            display_name=model.display_name,
            category=model.category,
            capabilities=sorted(model.capabilities),
            cost_per_1k_input_tokens=model.cost_per_1k_input_tokens,
            cost_per_1k_output_tokens=model.cost_per_1k_output_tokens,
            average_latency_ms=model.average_latency_ms,
            priority=model.priority,
            context_window=model.context_window,
            max_output_tokens=model.max_output_tokens,
            supports_streaming=model.supports_streaming,
            supports_function_calling=model.supports_function_calling,
            supports_vision=model.supports_vision,
            supports_audio=model.supports_audio,
            reasoning_score=model.reasoning_score,
            speed_score=model.speed_score,
            quality_score=model.quality_score,
            enabled=model.enabled and provider_manager.is_active(model.provider_id),
            deprecated=model.deprecated,
        )
        for model in model_registry.list_models(
            provider=provider_id,
            category=category,
            enabled_only=enabled_only,
        )
    ]


@router.get("/models/{provider_id}/{model_id}", response_model=ModelResponse, summary="Get model metadata")
async def get_model_detail(provider_id: str, model_id: str, user: User = Depends(require_permission("view_models"))) -> ModelResponse:
    """Return metadata for a single model by provider and model identifier."""
    try:
        model = model_registry.get_model(provider_id, model_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{provider_id}/{model_id}' not found in registry",
        )
    return ModelResponse(
        provider_id=model.provider_id,
        provider_name=model.provider_name,
        model_id=model.model_id,
        display_name=model.display_name,
        category=model.category,
        capabilities=sorted(model.capabilities),
        cost_per_1k_input_tokens=model.cost_per_1k_input_tokens,
        cost_per_1k_output_tokens=model.cost_per_1k_output_tokens,
        average_latency_ms=model.average_latency_ms,
        priority=model.priority,
        context_window=model.context_window,
        max_output_tokens=model.max_output_tokens,
        supports_streaming=model.supports_streaming,
        supports_function_calling=model.supports_function_calling,
        supports_vision=model.supports_vision,
        supports_audio=model.supports_audio,
        reasoning_score=model.reasoning_score,
        speed_score=model.speed_score,
        quality_score=model.quality_score,
        enabled=model.enabled,
        deprecated=model.deprecated,
    )
