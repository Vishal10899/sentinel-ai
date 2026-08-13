"""Immutable value objects for side-effect-free cost estimation and comparison."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CostEstimate:
    """Estimated token cost for one provider and model combination."""

    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost: Decimal
    daily_forecast_usd: Decimal = Decimal("0.0")
    monthly_forecast_usd: Decimal = Decimal("0.0")


@dataclass(frozen=True, slots=True)
class CostComparison:
    """Relative cost information derived from a collection of estimates."""

    cheapest: CostEstimate
    most_expensive: CostEstimate
    savings_amount: Decimal
    savings_percentage: Decimal
    recommendations: tuple["CostSavingsRecommendation", ...] = ()


@dataclass(frozen=True, slots=True)
class CostSavingsRecommendation:
    """Cost optimization recommendation comparing a model to cheaper alternatives."""

    current_model: str
    recommended_model: str
    savings_percentage: Decimal
    savings_amount_usd: Decimal
    suggestion_text: str


@dataclass(frozen=True, slots=True)
class BudgetStatus:
    """Workspace budget status, percentage utilization, and warning triggers."""

    workspace_id: str
    monthly_budget_usd: Decimal
    current_spend_usd: Decimal
    percentage_used: Decimal
    warning_status: str  # "normal", "warning_80", "warning_90", "exceeded"
    hard_stop_triggered: bool = False
