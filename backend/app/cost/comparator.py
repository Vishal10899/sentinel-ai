"""Cost Comparison Engine.

Evaluates "What would this request cost on every available model in the catalog?"
Generates model cost rankings, cheapest candidate, baseline comparison, and savings amounts.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from app.cost.pricing_engine import DetailedCostEstimate, pricing_engine
from app.models_registry import model_registry


@dataclass(frozen=True, slots=True)
class ModelCostComparisonItem:
    """Cost comparison item for a single catalog model."""

    provider_id: str
    model_id: str
    display_name: str
    rank: int
    cost_estimate: DetailedCostEstimate
    savings_vs_baseline_pct: float
    savings_vs_baseline_usd: float

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "display_name": self.display_name,
            "rank": self.rank,
            "cost_estimate": self.cost_estimate.to_dict(),
            "savings_vs_baseline_pct": self.savings_vs_baseline_pct,
            "savings_vs_baseline_usd": self.savings_vs_baseline_usd,
        }


@dataclass(frozen=True, slots=True)
class CostComparisonReport:
    """Full cross-model cost comparison matrix report."""

    prompt_tokens: int
    completion_tokens: int
    baseline_model: str
    baseline_cost_usd: float
    cheapest_model: str
    cheapest_cost_usd: float
    most_expensive_model: str
    most_expensive_cost_usd: float
    max_savings_pct: float
    max_savings_usd: float
    comparisons: tuple[ModelCostComparisonItem, ...]

    def to_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "baseline_model": self.baseline_model,
            "baseline_cost_usd": self.baseline_cost_usd,
            "cheapest_model": self.cheapest_model,
            "cheapest_cost_usd": self.cheapest_cost_usd,
            "most_expensive_model": self.most_expensive_model,
            "most_expensive_cost_usd": self.most_expensive_cost_usd,
            "max_savings_pct": self.max_savings_pct,
            "max_savings_usd": self.max_savings_usd,
            "comparisons": [c.to_dict() for c in self.comparisons],
        }


class CostComparator:
    """Cross-model cost evaluation and comparison engine (< 5ms)."""

    def compare_all(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        baseline_provider: str = "openai",
        baseline_model: str = "gpt-4o",
    ) -> CostComparisonReport:
        """Compare request cost across all enabled catalog models."""
        models = [m for m in model_registry.list_models() if m.enabled and not m.deprecated]
        if not models:
            raise ValueError("No enabled models in registry for comparison.")

        # Baseline cost
        try:
            baseline_est = pricing_engine.calculate_cost(
                baseline_provider, baseline_model, prompt_tokens, completion_tokens
            )
            baseline_usd = float(baseline_est.total_cost_usd)
        except KeyError:
            baseline_usd = 0.0025 * (prompt_tokens / 1000.0) + 0.010 * (completion_tokens / 1000.0)

        estimates = []
        for m in models:
            est = pricing_engine.calculate_cost(
                m.provider_id, m.model_id, prompt_tokens, completion_tokens
            )
            estimates.append((m, est))

        # Sort by total cost ascending
        estimates.sort(key=lambda item: item[1].total_cost_usd)

        comparison_items = []
        for idx, (m, est) in enumerate(estimates):
            cost_val = float(est.total_cost_usd)
            savings_usd = round(max(baseline_usd - cost_val, 0.0), 6)
            savings_pct = (
                round(((baseline_usd - cost_val) / baseline_usd) * 100.0, 1)
                if baseline_usd > 0 and cost_val < baseline_usd
                else 0.0
            )

            comparison_items.append(
                ModelCostComparisonItem(
                    provider_id=m.provider_id,
                    model_id=m.model_id,
                    display_name=m.display_name,
                    rank=idx + 1,
                    cost_estimate=est,
                    savings_vs_baseline_pct=savings_pct,
                    savings_vs_baseline_usd=savings_usd,
                )
            )

        cheapest = comparison_items[0]
        most_expensive = comparison_items[-1]

        return CostComparisonReport(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            baseline_model=f"{baseline_provider}/{baseline_model}",
            baseline_cost_usd=round(baseline_usd, 6),
            cheapest_model=f"{cheapest.provider_id}/{cheapest.model_id}",
            cheapest_cost_usd=float(cheapest.cost_estimate.total_cost_usd),
            most_expensive_model=f"{most_expensive.provider_id}/{most_expensive.model_id}",
            most_expensive_cost_usd=float(most_expensive.cost_estimate.total_cost_usd),
            max_savings_pct=cheapest.savings_vs_baseline_pct,
            max_savings_usd=cheapest.savings_vs_baseline_usd,
            comparisons=tuple(comparison_items),
        )


cost_comparator = CostComparator()
