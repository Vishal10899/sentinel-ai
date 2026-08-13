"""Enterprise Semantic Cache Management API Router."""

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import current_user, require_permission
from app.cache.semantic import semantic_cache
from app.models.user import User

router = APIRouter(prefix="/cache", tags=["cache"])


class InvalidateCacheRequest(BaseModel):
    workspace_id: str | None = None


class WarmCacheRequest(BaseModel):
    workspace_id: str = "default"
    prompt: str
    response_text: str
    provider_id: str = "openai"
    model_id: str = "gpt-4o"
    estimated_cost_usd: float = 0.001
    latency_ms: float = 250.0
    total_tokens: int = 150


@router.get("/stats", summary="Get semantic cache statistics")
async def get_cache_stats(user: User = Depends(current_user)):
    """Retrieve hit rate, exact hits, semantic hits, latency saved, and cost saved telemetry."""
    return semantic_cache.get_metrics()


@router.post("/invalidate", summary="Invalidate cache entries")
async def invalidate_cache(request: InvalidateCacheRequest | None = None, user: User = Depends(require_permission("cache.manage"))):
    """Clear semantic cache entries for a specific workspace or all workspaces."""
    ws_id = request.workspace_id if request else None
    count = semantic_cache.invalidate(workspace_id=ws_id)
    return {
        "status": "success",
        "invalidated_count": count,
        "workspace_id": ws_id or "all",
    }


@router.post("/warm", status_code=status.HTTP_201_CREATED, summary="Pre-warm semantic cache")
async def warm_cache(request: WarmCacheRequest, user: User = Depends(require_permission("cache.manage"))):

    """Seed cache with high-frequency prompts to optimize latency and eliminate redundant LLM costs."""
    entry = semantic_cache.set(
        prompt=request.prompt,
        response_text=request.response_text,
        workspace_id=request.workspace_id,
        provider_id=request.provider_id,
        model_id=request.model_id,
        estimated_cost_usd=request.estimated_cost_usd,
        latency_ms=request.latency_ms,
        total_tokens=request.total_tokens,
    )
    return {
        "status": "success",
        "entry": entry.to_dict(),
    }
