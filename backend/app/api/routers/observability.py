"""Enterprise Observability REST API Router."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.dependencies import current_user
from app.models.user import User
from app.observability import metrics_aggregator, observability_repository, trace_engine

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/traces", summary="List execution traces")
@router.get("/timeline", summary="Get live execution timeline")
async def get_live_timeline(
    workspace_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """Retrieve live execution trace timeline records."""
    traces = observability_repository.search_traces(workspace_id=workspace_id, limit=limit)
    return [t.to_dict() for t in traces]


@router.get("/traces/{trace_id}", summary="Get trace details")
async def get_trace_details(trace_id: str, user: User = Depends(current_user)):
    """Retrieve detailed trace record including hierarchical execution spans and stages."""
    trace = observability_repository.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Trace '{trace_id}' not found.")
    return trace.to_dict()


@router.get("/metrics", summary="Get overall aggregated control plane metrics")
async def get_metrics(workspace_id: str = Query(default="default"), window_seconds: int = Query(default=3600)):
    """Retrieve aggregated throughput (RPM/RPS, TPM/TPS), SLAs, and cost metrics (< 5ms)."""
    report = metrics_aggregator.aggregate(workspace_id=workspace_id, window_seconds=window_seconds)
    return report.to_dict()


@router.get("/providers", summary="Get provider analytics")
@router.get("/providers/health", summary="Get provider health status analytics")
@router.get("/analytics/providers", summary="Get provider health & SLA analytics")
async def get_provider_analytics():
    """Retrieve provider health status, P95/P99 latency, and availability metrics."""
    health_list = observability_repository.get_provider_health()
    return [h.to_dict() for h in health_list]


@router.get("/traces/{trace_id}/replay", summary="Get request replay snapshot")
async def get_request_replay(trace_id: str, user_id: str = Query(default="admin")):
    """Generate request replay snapshot for debugging and auditing."""
    trace = observability_repository.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Trace '{trace_id}' not found.")
    return {
        "trace_id": trace.trace_id,
        "conversation_id": trace.conversation_id,
        "workspace_id": trace.workspace_id,
        "prompt": trace.prompt,
        "provider_id": trace.provider_id,
        "model_id": trace.model_id,
        "status": trace.status,
        "response": trace.response,
        "spans": [s.to_dict() for s in trace.spans],
    }


@router.get("/alerts", summary="Get operational alerts")
async def get_operational_alerts():
    """Retrieve real-time operational alerts for latency spikes, error rates, and provider outages."""
    health_list = observability_repository.get_provider_health()
    alerts = []
    for h in health_list:
        if h.status == "DOWN":
            alerts.append({
                "alert_id": f"alert_{h.provider_id}_down",
                "severity": "CRITICAL",
                "provider_id": h.provider_id,
                "title": f"Provider {h.provider_name} Offline",
                "message": f"Provider {h.provider_name} success rate dropped below threshold ({h.success_rate}%).",
            })
        elif h.status == "DEGRADED":
            alerts.append({
                "alert_id": f"alert_{h.provider_id}_degraded",
                "severity": "WARNING",
                "provider_id": h.provider_id,
                "title": f"Provider {h.provider_name} Degraded",
                "message": f"Provider {h.provider_name} experiencing elevated latency (P95: {h.p95_latency_ms}ms).",
            })
    return alerts


@router.get("/models", summary="Get model usage analytics")
async def get_model_analytics(workspace_id: str = Query(default="default"), window_seconds: int = Query(default=3600)):
    """Retrieve model usage analytics and token counts."""
    report = metrics_aggregator.aggregate(workspace_id=workspace_id, window_seconds=window_seconds)
    return {
        "cost_by_model": report.cost_by_model,
        "total_tokens": report.total_tokens,
        "tokens_per_minute": report.tokens_per_minute,
    }


@router.get("/cost", summary="Get cost breakdown analytics")
@router.get("/analytics/cost", summary="Get cost breakdown analytics")
async def get_cost_analytics(workspace_id: str = Query(default="default"), window_seconds: int = Query(default=3600)):
    """Retrieve cost breakdown by provider, model, and total spend USD (< 5ms)."""
    report = metrics_aggregator.aggregate(workspace_id=workspace_id, window_seconds=window_seconds)
    return {
        "total_cost_usd": report.total_cost_usd,
        "cost_by_provider": report.cost_by_provider,
        "cost_by_model": report.cost_by_model,
        "total_tokens": report.total_tokens,
        "tokens_per_minute": report.tokens_per_minute,
    }


@router.get("/latency", summary="Get latency percentiles analytics")
@router.get("/analytics/latency", summary="Get latency percentiles analytics")
async def get_latency_analytics(workspace_id: str = Query(default="default"), window_seconds: int = Query(default=3600)):
    """Retrieve P50, P90, P95, P99 latency percentiles and throughput (< 5ms)."""
    report = metrics_aggregator.aggregate(workspace_id=workspace_id, window_seconds=window_seconds)
    return {
        "requests_per_minute": report.requests_per_minute,
        "requests_per_second": report.requests_per_second,
        "latency_percentiles": report.latency_percentiles.to_dict(),
    }


@router.get("/timeline/retries", summary="Get retry & failover timeline")
async def get_retry_failover_timeline(limit: int = Query(default=100)):
    """Retrieve requests that triggered retries or provider failovers."""
    traces = observability_repository.list_traces(limit=500)
    retry_failover_traces = [
        t.to_dict() for t in traces if t.retry_count > 0 or t.failover_count > 0
    ][:limit]
    return retry_failover_traces


@router.get("/errors", summary="Get error dashboard analytics")
async def get_error_dashboard(workspace_id: str = Query(default="default"), window_seconds: int = Query(default=3600)):
    """Retrieve error rate classification summary (Rate Limits 429, Auth 401/403, Server 500/503, Timeout 504)."""
    report = metrics_aggregator.aggregate(workspace_id=workspace_id, window_seconds=window_seconds)
    return report.error_summary.to_dict()
