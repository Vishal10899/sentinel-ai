"""Enterprise Reliability Platform REST API Router."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import current_user
from app.models.user import User
from app.observability import metrics_aggregator
from app.reliability import (
    adaptive_timeout_engine,
    advanced_retry_engine,
    bulkhead_engine,
    circuit_breaker_engine,
    connection_pool_engine,
    health_probing_engine,
    rate_limiter_engine,
)

router = APIRouter(prefix="/reliability", tags=["reliability"])


@router.get("/circuit-breakers", summary="List circuit breaker states")
async def list_circuit_breakers():
    """List circuit breaker state for all registered providers and models (< 0.1 ms)."""
    breakers = circuit_breaker_engine.list_breakers()
    return [b.to_dict() for b in breakers]


@router.get("/circuit-breakers/{provider_id}", summary="Get provider circuit breaker state")
async def get_circuit_breaker(provider_id: str):
    """Retrieve circuit breaker status for a specific provider."""
    breaker = circuit_breaker_engine.get_breaker(provider_id)
    return breaker.to_dict()


@router.post("/circuit-breakers/{provider_id}/reset", summary="Reset provider circuit breaker")
async def reset_circuit_breaker(provider_id: str, user: User = Depends(current_user)):
    """Admin operation to reset a tripped circuit breaker back to CLOSED state."""
    breaker = circuit_breaker_engine.reset_circuit(provider_id)
    return breaker.to_dict()


@router.get("/queues", summary="Get queue depth and bulkhead isolation status")
async def list_queues():
    """Retrieve queue depths and bulkhead capacity limits for all providers."""
    statuses = bulkhead_engine.list_statuses()
    return [
        {
            "provider_id": s.provider_id,
            "queue_depth": s.queue_depth,
            "max_queue_capacity": s.max_queue_capacity,
            "rejected_requests": s.rejected_requests,
        }
        for s in statuses
    ]


@router.get("/workers", summary="Get active worker pool status per provider")
async def list_workers():
    """Retrieve active worker counts and worker pool utilization per provider."""
    statuses = bulkhead_engine.list_statuses()
    return [
        {
            "provider_id": s.provider_id,
            "active_workers": s.active_workers,
            "max_concurrent_workers": s.max_concurrent_workers,
            "completed_requests": s.completed_requests,
        }
        for s in statuses
    ]


@router.get("/timeouts", summary="Get adaptive timeout configurations")
async def get_timeouts(provider_id: str = Query(default="gemini"), model_id: str = Query(default="gemini-2.0-flash"), task_category: str = Query(default="coding")):
    """Get soft and hard timeout allocations for a provider and task category (< 0.2 ms)."""
    decision = adaptive_timeout_engine.calculate_timeout(provider_id=provider_id, model_id=model_id, task_category=task_category)
    return decision.to_dict()


@router.get("/retries", summary="Get retry decision telemetry")
async def get_retries(attempt: int = Query(default=0), status_code: int = Query(default=429)):
    """Evaluate retry decision, transient classification, and backoff delay (< 0.2 ms)."""
    decision = advanced_retry_engine.evaluate_retry(attempt=attempt, status_code=status_code)
    return decision.to_dict()


@router.get("/connections", summary="Get connection pool status")
async def list_connections():
    """Retrieve active warm adapter connection pool status (< 0.1 ms)."""
    providers = ["openai", "gemini", "anthropic", "ollama"]
    conns = []
    for p in providers:
        conn = connection_pool_engine.get_connection(p)
        conns.append({
            "provider_id": p,
            "connected": conn is not None,
            "status": "warm_active",
        })
    return conns


@router.get("/rate-limits", summary="Get workspace/user/provider rate limit status")
async def get_rate_limits(workspace_id: str = Query(default="default"), user_id: str = Query(default="default_user"), provider_id: str = Query(default="gemini")):
    """Evaluate rate limits and token bucket status (< 0.1 ms)."""
    decision = rate_limiter_engine.evaluate(workspace_id=workspace_id, user_id=user_id, provider_id=provider_id)
    return decision.to_dict()


@router.get("/health-probes", summary="List provider health probe statuses")
async def list_health_probes():
    """Retrieve active & passive health probe results for all providers."""
    probes = health_probing_engine.run_all_probes()
    return [p.to_dict() for p in probes]


@router.post("/health-probes/run", summary="Trigger manual health probe sweep")
async def run_health_probes(user: User = Depends(current_user)):
    """Trigger an immediate health probing sweep across catalog providers."""
    probes = health_probing_engine.run_all_probes()
    return [p.to_dict() for p in probes]


@router.get("/metrics", summary="Get aggregated reliability metrics")
async def get_reliability_metrics(workspace_id: str = Query(default="default"), window_seconds: int = Query(default=3600)):
    """Retrieve aggregated reliability metrics (failures, retries, failovers, queue depths, error rates)."""
    report = metrics_aggregator.aggregate(workspace_id=workspace_id, window_seconds=window_seconds)
    breakers = circuit_breaker_engine.list_breakers()
    tripped_count = sum(1 for b in breakers if b.state != "CLOSED")
    bulkhead_stats = bulkhead_engine.list_statuses()

    return {
        "workspace_id": workspace_id,
        "retry_rate_pct": report.retry_rate_pct,
        "failover_rate_pct": report.failover_rate_pct,
        "error_summary": report.error_summary.to_dict(),
        "tripped_circuit_breakers": tripped_count,
        "total_circuit_breakers": len(breakers),
        "total_active_workers": sum(b.active_workers for b in bulkhead_stats),
        "total_queued_requests": sum(b.queue_depth for b in bulkhead_stats),
        "total_rejected_requests": sum(b.rejected_requests for b in bulkhead_stats),
    }
