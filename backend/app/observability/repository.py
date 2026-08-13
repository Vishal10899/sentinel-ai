import time
from uuid import uuid4
from typing import Any

from app.observability.models import ProviderHealthStatus, RequestReplaySnapshot, TraceRecord


class ObservabilityRepository:
    """Repository storing distributed traces, provider health metrics, and operational alerts."""

    def __init__(self, max_traces: int = 10000) -> None:
        self.max_traces = max_traces
        self._traces: dict[str, TraceRecord] = {}
        self._provider_records: dict[str, list[dict[str, Any]]] = {}

        self._seed_provider_health()

    def _seed_provider_health(self) -> None:
        """Initialize provider tracking for catalog providers."""
        providers = ["openai", "gemini", "anthropic", "ollama", "azure", "openrouter"]
        for p in providers:
            self._provider_records[p] = []

    def save_trace(self, trace: TraceRecord) -> None:
        """Store a trace record and update provider health telemetry."""
        self._traces[trace.trace_id] = trace

        # Record provider latency & status
        p_id = trace.provider_id
        if p_id not in self._provider_records:
            self._provider_records[p_id] = []
        
        self._provider_records[p_id].append({
            "timestamp": trace.created_at,
            "latency_ms": trace.total_latency_ms,
            "status": trace.status,
        })

    def get_trace(self, trace_id: str) -> TraceRecord | None:
        """Retrieve trace record by ID."""
        return self._traces.get(trace_id)

    def list_traces(self, limit: int = 100) -> list[TraceRecord]:
        """Return list of saved trace records."""
        return list(reversed(list(self._traces.values())))[:limit]

    def search_traces(
        self,
        workspace_id: str | None = None,
        user_id: str | None = None,
        provider_id: str | None = None,
        model_id: str | None = None,
        status: str | None = None,
        query: str | None = None,
        limit: int = 100,
    ) -> list[TraceRecord]:
        """Search and filter distributed trace records."""
        results = list(reversed(list(self._traces.values())))

        if workspace_id:
            results = [t for t in results if t.workspace_id == workspace_id]
        if user_id:
            results = [t for t in results if t.user_id == user_id]
        if provider_id:
            results = [t for t in results if t.provider_id.lower() == provider_id.lower()]
        if model_id:
            results = [t for t in results if t.model_id.lower() == model_id.lower()]
        if status:
            results = [t for t in results if t.status.lower() == status.lower()]
        if query:
            q = query.lower()
            results = [
                t for t in results
                if q in t.trace_id.lower() or q in t.prompt.lower() or q in t.model_id.lower()
            ]

        return results[:limit]

    def get_provider_health(self) -> list[ProviderHealthStatus]:
        """Calculate provider health status, latency P95/P99, and availability."""
        health_list = []
        for p_id, records in self._provider_records.items():
            total = len(records)
            if total == 0:
                health_list.append(ProviderHealthStatus(
                    provider_id=p_id,
                    provider_name=p_id.capitalize(),
                    total_requests=0,
                    successful_requests=0,
                    failed_requests=0,
                    avg_latency_ms=0.0,
                    p95_latency_ms=0.0,
                    p99_latency_ms=0.0,
                    success_rate=100.0,
                    status="HEALTHY",
                ))
                continue

            successes = [r for r in records if r["status"] == "SUCCESS"]
            failures = [r for r in records if r["status"] != "SUCCESS"]

            success_cnt = len(successes)
            fail_cnt = len(failures)
            success_rate = round((success_cnt / total) * 100, 1)

            latencies = sorted([r["latency_ms"] for r in records])
            avg_lat = round(sum(latencies) / total, 1) if latencies else 0.0
            
            p95_idx = int(total * 0.95)
            p99_idx = int(total * 0.99)
            p95_lat = round(latencies[min(p95_idx, total - 1)], 1) if latencies else 0.0
            p99_lat = round(latencies[min(p99_idx, total - 1)], 1) if latencies else 0.0

            p_status = "HEALTHY"
            if success_rate < 80.0:
                p_status = "DOWN"
            elif success_rate < 95.0 or p95_lat > 2500:
                p_status = "DEGRADED"

            last_success = max([r["timestamp"] for r in successes], default=None)

            health_list.append(ProviderHealthStatus(
                provider_id=p_id,
                provider_name=p_id.capitalize(),
                total_requests=total,
                successful_requests=success_cnt,
                failed_requests=fail_cnt,
                avg_latency_ms=avg_lat,
                p95_latency_ms=p95_lat,
                p99_latency_ms=p99_lat,
                success_rate=success_rate,
                status=p_status,
                last_successful_request_at=last_success,
            ))

        return health_list

    def get_metrics_summary(self) -> dict[str, Any]:
        """Calculate real-time operational dashboard metrics."""
        traces = list(self._traces.values())
        total_reqs = len(traces)
        if total_reqs == 0:
            return {
                "rpm": 0,
                "avg_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "error_rate": 0.0,
                "cache_hit_ratio": 0.0,
                "total_traces": 0,
            }

        latencies = sorted([t.total_latency_ms for t in traces])
        avg_lat = round(sum(latencies) / total_reqs, 1)
        p95_idx = int(total_reqs * 0.95)
        p99_idx = int(total_reqs * 0.99)
        p95_lat = round(latencies[min(p95_idx, total_reqs - 1)], 1)
        p99_lat = round(latencies[min(p99_idx, total_reqs - 1)], 1)

        errors = len([t for t in traces if t.status == "FAILED"])
        cache_hits = len([t for t in traces if t.cache_hit])

        error_rate = round((errors / total_reqs) * 100, 1)
        cache_hit_ratio = round((cache_hits / total_reqs) * 100, 1)

        return {
            "rpm": round(total_reqs / 60, 1),
            "avg_latency_ms": avg_lat,
            "p95_latency_ms": p95_lat,
            "p99_latency_ms": p99_lat,
            "error_rate": error_rate,
            "cache_hit_ratio": cache_hit_ratio,
            "total_traces": total_reqs,
        }


observability_repository = ObservabilityRepository()
