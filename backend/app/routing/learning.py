"""Continuous Learning Engine for Sentinel AI.

Stores anonymous execution metadata (prompt category, selected model, latency, cost, success/failure, cache usage)
and dynamically updates model scoring multipliers over time based on real execution performance.
Exposes extension hooks for future Verification Models, Consensus Aggregators, and Agent Collaboration.
"""

from dataclasses import dataclass, field
from collections import defaultdict
import time
from typing import Any, Callable


@dataclass(slots=True)
class ExecutionMetadata:
    """Anonymous execution metadata DTO."""

    prompt_category: str
    selected_provider: str
    selected_model: str
    latency_ms: float
    cost_usd: float
    success: bool
    failure: bool
    cache_used: bool
    timestamp: float = field(default_factory=time.time)


@dataclass(slots=True)
class PerformanceAggregate:
    """Aggregated real-time metrics per (category, provider, model)."""

    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_latency_ms: float = 0.0
    total_cost_usd: float = 0.0
    cache_hits: int = 0

    @property
    def success_rate(self) -> float:
        if self.total_executions == 0:
            return 1.0
        return self.successful_executions / self.total_executions

    @property
    def avg_latency_ms(self) -> float:
        if self.total_executions == 0:
            return 0.0
        return self.total_latency_ms / self.total_executions

    @property
    def avg_cost_usd(self) -> float:
        if self.total_executions == 0:
            return 0.0
        return self.total_cost_usd / self.total_executions


class ContinuousLearningEngine:
    """Enterprise Continuous Learning & Dynamic Routing Optimization Engine."""

    def __init__(self, max_history: int = 1000) -> None:
        self._history: list[ExecutionMetadata] = []
        self._max_history = max_history
        self._aggregates: dict[tuple[str, str, str], PerformanceAggregate] = defaultdict(PerformanceAggregate)

        # Future architecture extension hooks
        self._verification_hooks: list[Callable[[str, str], float]] = []
        self._consensus_hooks: list[Callable[[list[dict[str, Any]]], dict[str, Any]]] = []
        self._agent_collaboration_hooks: list[Callable[[str, dict[str, Any]], dict[str, Any]]] = []

    def record_execution(self, meta: ExecutionMetadata) -> None:
        """Record execution metadata anonymously and update continuous learning statistics."""
        self._history.append(meta)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        key = (meta.prompt_category.lower(), meta.selected_provider.lower(), meta.selected_model.lower())
        agg = self._aggregates[key]
        agg.total_executions += 1
        if meta.success:
            agg.successful_executions += 1
        if meta.failure:
            agg.failed_executions += 1
        agg.total_latency_ms += meta.latency_ms
        agg.total_cost_usd += meta.cost_usd
        if meta.cache_used:
            agg.cache_hits += 1

    def get_learning_multiplier(self, provider_id: str, model_id: str, category: str) -> float:
        """Calculate dynamic scoring multiplier (0.5 to 1.3) based on historical performance telemetry."""
        key = (category.lower(), provider_id.lower(), model_id.lower())
        agg = self._aggregates.get(key)
        if not agg or agg.total_executions == 0:
            return 1.0

        success_mult = agg.success_rate
        latency_boost = 1.0
        if agg.avg_latency_ms > 0:
            if agg.avg_latency_ms < 1500:
                latency_boost = 1.15
            elif agg.avg_latency_ms > 5000:
                latency_boost = 0.85

        final_mult = round(success_mult * latency_boost, 2)
        return max(0.5, min(1.3, final_mult))

    def register_verification_hook(self, hook: Callable[[str, str], float]) -> None:
        """Architecture extension hook for future Verification Models."""
        self._verification_hooks.append(hook)

    def register_consensus_hook(self, hook: Callable[[list[dict[str, Any]]], dict[str, Any]]) -> None:
        """Architecture extension hook for future Consensus Response aggregators."""
        self._consensus_hooks.append(hook)

    def register_agent_collaboration_hook(self, hook: Callable[[str, dict[str, Any]], dict[str, Any]]) -> None:
        """Architecture extension hook for future Multi-Agent Collaboration."""
        self._agent_collaboration_hooks.append(hook)

    def get_telemetry_summary(self) -> dict[str, Any]:
        """Return anonymous aggregated execution telemetry for governance dashboards."""
        stats = []
        for (cat, prov, mod), agg in self._aggregates.items():
            stats.append(
                {
                    "category": cat,
                    "provider_id": prov,
                    "model_id": mod,
                    "total_executions": agg.total_executions,
                    "success_rate": round(agg.success_rate * 100.0, 1),
                    "avg_latency_ms": round(agg.avg_latency_ms, 1),
                    "avg_cost_usd": round(agg.avg_cost_usd, 6),
                    "cache_hits": agg.cache_hits,
                }
            )
        return {
            "total_recorded_events": len(self._history),
            "telemetry_stats": stats,
            "architecture_hooks": {
                "verification_models_active": len(self._verification_hooks),
                "consensus_aggregators_active": len(self._consensus_hooks),
                "agent_collaborators_active": len(self._agent_collaboration_hooks),
            },
        }


continuous_learning_engine = ContinuousLearningEngine()
