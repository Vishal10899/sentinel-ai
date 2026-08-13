"""Enterprise Prometheus Metrics Telemetry for Sentinel AI v1.0.0."""

import time
from typing import Any

from app.observability.repository import observability_repository


class PrometheusMetricsExporter:
    """Prometheus Exposition Format Metrics Exporter."""

    def generate_metrics_payload(self) -> str:
        """Export real-time platform telemetry metrics in Prometheus text exposition format."""
        summary = observability_repository.get_metrics_summary()
        provider_health = observability_repository.get_provider_health()

        lines = [
            "# HELP sentinel_requests_total Total HTTP requests processed by Sentinel AI control plane",
            "# TYPE sentinel_requests_total counter",
            f"sentinel_requests_total {summary.get('total_traces', 0)}",
            "",
            "# HELP sentinel_requests_rpm Current requests per minute throughput",
            "# TYPE sentinel_requests_rpm gauge",
            f"sentinel_requests_rpm {summary.get('rpm', 0)}",
            "",
            "# HELP sentinel_latency_p95_ms P95 latency in milliseconds",
            "# TYPE sentinel_latency_p95_ms gauge",
            f"sentinel_latency_p95_ms {summary.get('p95_latency_ms', 0.0)}",
            "",
            "# HELP sentinel_latency_p99_ms P99 latency in milliseconds",
            "# TYPE sentinel_latency_p99_ms gauge",
            f"sentinel_latency_p99_ms {summary.get('p99_latency_ms', 0.0)}",
            "",
            "# HELP sentinel_error_rate_percentage Percentage of requests resulting in error or block",
            "# TYPE sentinel_error_rate_percentage gauge",
            f"sentinel_error_rate_percentage {summary.get('error_rate', 0.0)}",
            "",
            "# HELP sentinel_cache_hit_ratio Percentage of queries served sub-10ms via semantic cache",
            "# TYPE sentinel_cache_hit_ratio gauge",
            f"sentinel_cache_hit_ratio {summary.get('cache_hit_ratio', 0.0)}",
            "",
        ]

        for p in provider_health:
            lines.extend([
                f'sentinel_provider_success_rate{{provider="{p.provider_id}"}} {p.success_rate}',
                f'sentinel_provider_p95_latency_ms{{provider="{p.provider_id}"}} {p.p95_latency_ms}',
            ])

        return "\n".join(lines) + "\n"


metrics_exporter = PrometheusMetricsExporter()
