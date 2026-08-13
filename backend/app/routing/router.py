"""High-level routing facade that composes selection and strategy policies."""

from collections.abc import Sequence

from app.routing.selector import ModelSelector
from app.routing.strategies import BalancedStrategy, RoutingStrategy
from app.routing.types import CandidateScore, ModelInfo, RoutingDecisionExplanation, TaskCategory


class IntelligentRouter:
    """Choose a provider from caller-supplied model metadata with health awareness and detailed decision tracing."""

    def __init__(
        self,
        strategy: RoutingStrategy | None = None,
        selector: ModelSelector | None = None,
    ) -> None:
        self._strategy = strategy or BalancedStrategy()
        self._selector = selector or ModelSelector()

    def select_model(
        self,
        task_type: TaskCategory,
        available_providers: Sequence[ModelInfo],
    ) -> ModelInfo:
        """Select one compatible model for a task using the configured strategy and health awareness."""
        explanation = self.evaluate_with_explanation(task_type, available_providers)
        selected = next(
            (m for m in available_providers if m.provider == explanation.selected_provider and m.model_name == explanation.selected_model),
            None,
        )
        if not selected:
            # Fallback to selector + strategy
            candidates = self._selector.compatible_models(task_type, available_providers)
            if not candidates:
                raise ValueError(f"No provider supports task category '{task_type}'")
            return self._strategy.select(candidates)
        return selected

    def evaluate_with_explanation(
        self,
        task_type: TaskCategory,
        available_providers: Sequence[ModelInfo],
        strategy_name: str = "balanced",
    ) -> RoutingDecisionExplanation:
        """Evaluate all candidates, filter unhealthy providers (circuit breaker), score, and generate decision trace."""
        compatible = self._selector.compatible_models(task_type, available_providers)
        if not compatible:
            raise ValueError(f"No active provider supports task category '{task_type}'")

        from app.providers.manager import provider_manager

        # Circuit breaker: filter out unhealthy, disabled, or unconfigured providers
        active_candidates = []
        bypassed_providers = []
        for model in compatible:
            if not provider_manager.is_active(model.provider) or model.provider_status in ("unhealthy", "disabled", "unconfigured", "DOWN") or model.provider_failures >= 3:
                bypassed_providers.append(f"{model.provider}/{model.model_name} (Status: {model.provider_status})")
            else:
                active_candidates.append(model)

        failover_triggered = False
        if not active_candidates:
            # Fall back strictly to models from active providers
            active_candidates = [
                m for m in compatible
                if provider_manager.is_active(m.provider) and m.provider_status not in ("disabled", "unconfigured", "DOWN")
            ]
            failover_triggered = True

        if not active_candidates:
            raise ValueError(f"No active provider available for task category '{task_type}'")

        selected = self._strategy.select(active_candidates)

        # Generate ranked candidate scores for explanation
        max_cost = max((m.cost_per_1k_tokens for m in active_candidates), default=1.0) or 1.0
        max_lat = max((m.latency for m in active_candidates), default=1.0) or 1.0

        scored_candidates = []
        for model in compatible:
            is_bypassed = model not in active_candidates
            norm_cost = (1.0 - (model.cost_per_1k_tokens / max_cost)) * 30.0 if max_cost > 0 else 30.0
            norm_lat = (1.0 - (model.latency / max_lat)) * 30.0 if max_lat > 0 else 30.0
            norm_qual = (model.quality_score / 100.0) * 40.0
            score = round(norm_cost + norm_lat + norm_qual, 1)

            reason = (
                f"Selected: Optimal {strategy_name} score ({score}/100) with {model.latency}ms SLA."
                if model == selected
                else ("Bypassed by circuit breaker (provider health issue)." if is_bypassed else f"Scored {score}/100.")
            )

            scored_candidates.append(
                CandidateScore(
                    provider=model.provider,
                    model_name=model.model_name,
                    overall_score=score,
                    rank=0, # set after sort
                    cost_per_1k_tokens=model.cost_per_1k_tokens,
                    latency=model.latency,
                    quality_score=model.quality_score,
                    reasoning_score=model.reasoning_score,
                    status="bypassed" if is_bypassed else "active",
                    reason=reason,
                )
            )

        # Sort and rank
        scored_candidates.sort(key=lambda c: (-c.overall_score, c.latency))
        ranked = tuple(
            CandidateScore(
                provider=c.provider,
                model_name=c.model_name,
                overall_score=c.overall_score,
                rank=idx + 1,
                cost_per_1k_tokens=c.cost_per_1k_tokens,
                latency=c.latency,
                quality_score=c.quality_score,
                reasoning_score=c.reasoning_score,
                status=c.status,
                reason=c.reason,
            )
            for idx, c in enumerate(scored_candidates)
        )

        primary_reason = (
            f"Selected {selected.provider}/{selected.model_name} using '{strategy_name}' strategy. "
            f"Model offers {selected.latency}ms SLA latency, ${selected.cost_per_1k_tokens}/1K token rate, "
            f"and {selected.quality_score}% quality score."
        )

        return RoutingDecisionExplanation(
            selected_provider=selected.provider,
            selected_model=selected.model_name,
            strategy_used=strategy_name,
            primary_reason=primary_reason,
            ranked_candidates=ranked,
            failover_triggered=failover_triggered,
            circuit_breaker_bypassed=tuple(bypassed_providers),
        )

    def select_provider(
        self,
        task_type: TaskCategory,
        available_providers: Sequence[ModelInfo],
    ) -> str:
        """Return the selected provider identifier for the requested task."""
        return self.select_model(task_type, available_providers).provider
