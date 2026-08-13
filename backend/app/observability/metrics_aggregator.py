"""Enterprise Telemetry & Performance Metrics Aggregator.

Calculates RPM/RPS, TPM/TPS, P50/P90/P95/P99 latency percentiles, cost breakdowns,
retry/failover rates, and error rate classifications in < 5ms processing time.
"""

from dataclasses import dataclass, field
import statistics
import time

from app.observability.repository import observability_repository


@dataclass(frozen=True, slots=True)
class LatencyPercentiles:
    """P50, P90, P95, P99 latency percentiles."""

    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    average_ms: float

    def to_dict(self) -> dict:
        return {
            "p50_ms": self.p50_ms,
            "p90_ms": self.p90_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "average_ms": self.average_ms,
        }


@dataclass(frozen=True, slots=True)
class ErrorClassificationSummary:
    """Error rate classification summary."""

    total_errors: int
    rate_limit_429: int
    auth_error_401_403: int
    server_error_500_503: int
    timeout_error_504: int
    error_rate_pct: float

    def to_dict(self) -> dict:
        return {
            "total_errors": self.total_errors,
            "rate_limit_429": self.rate_limit_429,
            "auth_error_401_403": self.auth_error_401_403,
            "server_error_500_503": self.server_error_500_503,
            "timeout_error_504": self.timeout_error_504,
            "error_rate_pct": self.error_rate_pct,
        }


@dataclass(frozen=True, slots=True)
class AggregatedMetricsReport:
    """Complete Control Plane Telemetry & Performance Report."""

    timestamp: float
    window_seconds: int
    total_requests: int
    requests_per_minute: float
    requests_per_second: float
    total_tokens: int
    tokens_per_minute: float
    total_cost_usd: float
    latency_percentiles: LatencyPercentiles
    error_summary: ErrorClassificationSummary
    retry_rate_pct: float
    failover_rate_pct: float
    cost_by_provider: dict[str, float]
    cost_by_model: dict[str, float]

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "window_seconds": self.window_seconds,
            "total_requests": self.total_requests,
            "requests_per_minute": self.requests_per_minute,
            "requests_per_second": self.requests_per_second,
            "total_tokens": self.total_tokens,
            "tokens_per_minute": self.tokens_per_minute,
            "total_cost_usd": self.total_cost_usd,
            "latency_percentiles": self.latency_percentiles.to_dict(),
            "error_summary": self.error_summary.to_dict(),
            "retry_rate_pct": self.retry_rate_pct,
            "failover_rate_pct": self.failover_rate_pct,
            "cost_by_provider": self.cost_by_provider,
            "cost_by_model": self.cost_by_model,
        }


class MetricsAggregator:
    """High-performance metrics aggregator (< 5ms)."""

    def aggregate(self, workspace_id: str = "default", window_seconds: int = 3600) -> AggregatedMetricsReport:
        """Aggregate Control Plane traces and compute throughput, SLAs, and cost metrics (< 5ms)."""
        now = time.time()
        cutoff = now - window_seconds

        traces = [t for t in observability_repository.list_traces(limit=5000) if t.created_at >= cutoff]

        total_reqs = len(traces)
        if total_reqs == 0:
            return AggregatedMetricsReport(
                timestamp=now,
                window_seconds=window_seconds,
                total_requests=0,
                requests_per_minute=0.0,
                requests_per_second=0.0,
                total_tokens=0,
                tokens_per_minute=0.0,
                total_cost_usd=0.0,
                latency_percentiles=LatencyPercentiles(0.0, 0.0, 0.0, 0.0, 0.0),
                error_summary=ErrorClassificationSummary(0, 0, 0, 0, 0, 0.0),
                retry_rate_pct=0.0,
                failover_rate_pct=0.0,
                cost_by_provider={},
                cost_by_model={},
            )

        minutes = max(window_seconds / 60.0, 1.0)
        rpm = round(total_reqs / minutes, 2)
        rps = round(total_reqs / window_seconds, 2)

        total_tokens = sum(t.tokens for t in traces)
        tpm = round(total_tokens / minutes, 2)
        total_cost = round(sum(t.cost_usd for t in traces), 6)

        # Latency Percentiles
        latencies = sorted([t.total_latency_ms for t in traces])
        n = len(latencies)
        avg_lat = round(statistics.mean(latencies), 2)
        p50 = round(latencies[int(n * 0.50)], 2)
        p90 = round(latencies[min(int(n * 0.90), n - 1)], 2)
        p95 = round(latencies[min(int(n * 0.95), n - 1)], 2)
        p99 = round(latencies[min(int(n * 0.99), n - 1)], 2)

        # Error Classification
        err_429 = sum(1 for t in traces if t.status_code == 429)
        err_auth = sum(1 for t in traces if t.status_code in (401, 403))
        err_500 = sum(1 for t in traces if t.status_code in (500, 502, 503))
        err_504 = sum(1 for t in traces if t.status_code == 504 or t.status == "TIMEOUT")
        total_errors = sum(1 for t in traces if t.status != "SUCCESS" or t.status_code >= 400)
        err_rate = round((total_errors / total_reqs) * 100.0, 2)

        # Retries & Failovers
        retries_count = sum(1 for t in traces if t.retry_count > 0)
        failovers_count = sum(1 for t in traces if t.failover_count > 0)
        retry_rate = round((retries_count / total_reqs) * 100.0, 2)
        failover_rate = round((failovers_count / total_reqs) * 100.0, 2)

        # Cost Breakdown by Provider & Model
        cost_by_prov: dict[str, float] = {}
        cost_by_mod: dict[str, float] = {}
        for t in traces:
            cost_by_prov[t.provider_id] = round(cost_by_prov.get(t.provider_id, 0.0) + t.cost_usd, 6)
            mod_key = f"{t.provider_id}/{t.model_id}"
            cost_by_mod[mod_key] = round(cost_by_mod.get(mod_key, 0.0) + t.cost_usd, 6)

        return AggregatedMetricsReport(
            timestamp=now,
            window_seconds=window_seconds,
            total_requests=total_reqs,
            requests_per_minute=rpm,
            requests_per_second=rps,
            total_tokens=total_tokens,
            tokens_per_minute=tpm,
            total_cost_usd=total_cost,
            latency_percentiles=LatencyPercentiles(p50, p90, p95, p99, avg_lat),
            error_summary=ErrorClassificationSummary(total_errors, err_429, err_auth, err_500, err_504, err_rate),
            retry_rate_pct=retry_rate,
            failover_rate_pct=failover_rate,
            cost_by_provider=cost_by_prov,
            cost_by_model=cost_by_mod,
        )


metrics_aggregator = MetricsAggregator()
