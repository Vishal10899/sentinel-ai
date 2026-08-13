"""Weighted Multi-Factor Scoring Engine for candidate model evaluation."""

from dataclasses import dataclass, field
from app.routing.classifier import TaskCategoryV2
from app.routing.complexity import ComplexityLevel
from app.routing.types import ModelInfo


@dataclass(frozen=True, slots=True)
class CandidateScoreBreakdown:
    """Detailed multi-factor breakdown score for a candidate model."""

    provider_id: str
    model_id: str
    overall_score: float
    rank: int
    task_match_score: float
    complexity_match_score: float
    latency_score: float
    cost_score: float
    health_score: float
    cost_per_1k_tokens: float
    latency_ms: float
    status: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "overall_score": self.overall_score,
            "rank": self.rank,
            "task_match_score": self.task_match_score,
            "complexity_match_score": self.complexity_match_score,
            "latency_score": self.latency_score,
            "cost_score": self.cost_score,
            "health_score": self.health_score,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
            "latency_ms": self.latency_ms,
            "status": self.status,
            "reason": self.reason,
        }


class MultiFactorScoringEngine:
    """Weighted multi-factor model evaluator and candidate ranker."""

    def __init__(
        self,
        task_match_weight: float = 0.30,
        complexity_weight: float = 0.20,
        latency_weight: float = 0.20,
        cost_weight: float = 0.15,
        health_weight: float = 0.15,
    ) -> None:
        self.task_match_weight = task_match_weight
        self.complexity_weight = complexity_weight
        self.latency_weight = latency_weight
        self.cost_weight = cost_weight
        self.health_weight = health_weight

    def _score_task_match(self, model: ModelInfo, task_category: TaskCategoryV2) -> float:
        """Score how well candidate capabilities match requested task category (0 to 100)."""
        cat_val = task_category.value.lower()
        if cat_val in ["coding", "code_review", "debugging", "sql"]:
            return model.reasoning_score * 0.6 + model.quality_score * 0.4
        elif cat_val in ["reasoning", "math", "security_review"]:
            return model.reasoning_score
        elif cat_val in ["translation", "summarization"]:
            return model.speed_score * 0.5 + model.quality_score * 0.5
        else:
            return model.quality_score

    def _score_complexity_match(self, model: ModelInfo, complexity: ComplexityLevel) -> float:
        """Score candidate suitability for task complexity level (0 to 100)."""
        if complexity == ComplexityLevel.VERY_COMPLEX:
            return model.reasoning_score * 0.7 + model.quality_score * 0.3
        elif complexity == ComplexityLevel.COMPLEX:
            return model.quality_score
        elif complexity == ComplexityLevel.MEDIUM:
            return (model.quality_score + model.speed_score) / 2.0
        else:  # SIMPLE
            # Simple tasks favor fast & low cost models
            return model.speed_score * 0.6 + (100.0 - min(model.cost_per_1k_tokens * 10.0, 100.0)) * 0.4

    def _score_latency(self, model: ModelInfo, min_lat: float, max_lat: float) -> float:
        """Normalize latency relative to pool (0 to 100, higher is faster)."""
        if max_lat <= min_lat:
            return 100.0
        norm = 1.0 - ((model.latency - min_lat) / (max_lat - min_lat))
        return round(norm * 100.0, 1)

    def _score_cost(self, model: ModelInfo, min_cost: float, max_cost: float) -> float:
        """Normalize cost relative to pool (0 to 100, higher is cheaper)."""
        if max_cost <= min_cost:
            return 100.0
        norm = 1.0 - ((model.cost_per_1k_tokens - min_cost) / (max_cost - min_cost))
        return round(norm * 100.0, 1)

    def _score_health(self, model: ModelInfo) -> float:
        """Score provider health and reliability (0 to 100)."""
        if model.provider_status.lower() in ["down", "unhealthy", "disabled"]:
            return 0.0
        failures = getattr(model, "provider_failures", 0)
        return max(100.0 - (failures * 25.0), 10.0)

    def evaluate(
        self,
        candidates: list[ModelInfo],
        task_category: TaskCategoryV2,
        complexity: ComplexityLevel,
        strategy_name: str = "balanced",
    ) -> list[CandidateScoreBreakdown]:
        """Evaluate candidate models and return ranked list of score breakdowns."""
        if not candidates:
            return []

        min_cost = min(m.cost_per_1k_tokens for m in candidates)
        max_cost = max(m.cost_per_1k_tokens for m in candidates)
        min_lat = min(m.latency for m in candidates)
        max_lat = max(m.latency for m in candidates)

        evaluated = []
        for model in candidates:
            task_score = self._score_task_match(model, task_category)
            comp_score = self._score_complexity_match(model, complexity)
            lat_score = self._score_latency(model, min_lat, max_lat)
            cost_score = self._score_cost(model, min_cost, max_cost)
            health_score = self._score_health(model)

            # Weight adjustments based on strategy
            t_w, c_w, l_w, cost_w, h_w = (
                self.task_match_weight,
                self.complexity_weight,
                self.latency_weight,
                self.cost_weight,
                self.health_weight,
            )

            if strategy_name == "cheapest":
                cost_w, l_w, t_w = 0.50, 0.20, 0.15
            elif strategy_name == "fastest":
                l_w, cost_w, t_w = 0.50, 0.15, 0.20
            elif strategy_name in ("highest_quality", "reasoning_optimized"):
                t_w, c_w, cost_w = 0.45, 0.30, 0.05

            from app.routing.learning import continuous_learning_engine
            learning_mult = continuous_learning_engine.get_learning_multiplier(
                model.provider, model.model_name, task_category.value
            )

            overall = round(
                (
                    (task_score * t_w)
                    + (comp_score * c_w)
                    + (lat_score * l_w)
                    + (cost_score * cost_w)
                    + (health_score * h_w)
                )
                * learning_mult,
                1,
            )

            status_str = "active" if health_score > 0 else "bypassed"
            reason = (
                f"Matched {task_category.value} ({task_score:.1f}) & {complexity.value} complexity ({comp_score:.1f}). "
                f"Latency: {model.latency}ms, Rate: ${model.cost_per_1k_tokens}/1K tokens."
            )

            evaluated.append(
                CandidateScoreBreakdown(
                    provider_id=model.provider,
                    model_id=model.model_name,
                    overall_score=overall,
                    rank=0,
                    task_match_score=round(task_score, 1),
                    complexity_match_score=round(comp_score, 1),
                    latency_score=round(lat_score, 1),
                    cost_score=round(cost_score, 1),
                    health_score=round(health_score, 1),
                    cost_per_1k_tokens=model.cost_per_1k_tokens,
                    latency_ms=model.latency,
                    status=status_str,
                    reason=reason,
                )
            )

        # Sort descending by overall score, tie-break by latency
        evaluated.sort(key=lambda item: (-item.overall_score, item.latency_ms))

        # Assign 1-indexed ranks
        ranked = [
            CandidateScoreBreakdown(
                provider_id=item.provider_id,
                model_id=item.model_id,
                overall_score=item.overall_score,
                rank=idx + 1,
                task_match_score=item.task_match_score,
                complexity_match_score=item.complexity_match_score,
                latency_score=item.latency_score,
                cost_score=item.cost_score,
                health_score=item.health_score,
                cost_per_1k_tokens=item.cost_per_1k_tokens,
                latency_ms=item.latency_ms,
                status=item.status,
                reason=item.reason,
            )
            for idx, item in enumerate(evaluated)
        ]
        return ranked


scoring_engine = MultiFactorScoringEngine()
