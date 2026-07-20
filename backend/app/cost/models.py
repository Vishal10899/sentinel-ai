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


@dataclass(frozen=True, slots=True)
class CostComparison:
    """Relative cost information derived from a collection of estimates."""

    cheapest: CostEstimate
    most_expensive: CostEstimate
    savings_amount: Decimal
    savings_percentage: Decimal
