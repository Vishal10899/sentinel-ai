"""Pure comparison logic for independently generated cost estimates."""

from collections.abc import Sequence
from decimal import Decimal

from app.cost.models import CostComparison, CostEstimate


class CostComparator:
    """Compare model estimates without retaining state or writing to storage."""

    def compare(self, estimates: Sequence[CostEstimate]) -> CostComparison:
        """Return cheapest, most expensive, and the savings between those estimates."""
        if not estimates:
            raise ValueError("At least one cost estimate is required")

        cheapest = min(estimates, key=lambda estimate: estimate.estimated_cost)
        most_expensive = max(estimates, key=lambda estimate: estimate.estimated_cost)
        savings_amount = most_expensive.estimated_cost - cheapest.estimated_cost
        savings_percentage = Decimal("0")

        if most_expensive.estimated_cost:
            savings_percentage = (savings_amount / most_expensive.estimated_cost) * 100

        return CostComparison(
            cheapest=cheapest,
            most_expensive=most_expensive,
            savings_amount=savings_amount,
            savings_percentage=savings_percentage,
        )
