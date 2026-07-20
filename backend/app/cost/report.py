"""Savings report builder based solely on in-memory cost estimates."""

from dataclasses import dataclass
from decimal import Decimal

from app.cost.models import CostComparison, CostEstimate


@dataclass(frozen=True, slots=True)
class SavingsReport:
    """Actionable, non-persistent summary of a selected model's estimated savings."""

    selected_model: str
    cheapest_model: str
    estimated_savings: Decimal
    recommendation: str

    @classmethod
    def create(
        cls,
        selected: CostEstimate,
        comparison: CostComparison,
    ) -> "SavingsReport":
        """Build a recommendation by comparing the selected model with the cheapest one."""
        cheapest = comparison.cheapest
        estimated_savings = max(
            selected.estimated_cost - cheapest.estimated_cost,
            Decimal("0"),
        )

        if selected == cheapest:
            recommendation = "The selected model is already the lowest-cost option."
        else:
            recommendation = (
                f"Select {cheapest.provider}/{cheapest.model} to reduce estimated cost."
            )

        return cls(
            selected_model=selected.model,
            cheapest_model=cheapest.model,
            estimated_savings=estimated_savings,
            recommendation=recommendation,
        )
