"""Composition layer that turns a token-cost calculation into a CostEstimate."""

from decimal import Decimal

from app.cost.calculator import CostCalculator
from app.cost.models import CostEstimate


class CostEstimator:
    """Build cost estimates with an injected calculator for straightforward unit tests."""

    def __init__(self, calculator: CostCalculator | None = None) -> None:
        self._calculator = calculator or CostCalculator()

    def estimate(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_per_1k_tokens: Decimal | float | str,
    ) -> CostEstimate:
        """Create one immutable estimate without retrieving prices or calling providers."""
        estimated_cost = self._calculator.calculate_cost(
            input_tokens,
            output_tokens,
            cost_per_1k_tokens,
        )
        return CostEstimate(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=estimated_cost,
        )

    def estimate_with_token_prices(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        input_cost_per_1k_tokens: Decimal | float | str,
        output_cost_per_1k_tokens: Decimal | float | str,
    ) -> CostEstimate:
        """Create an estimate from the separate input and output prices in the registry."""
        estimated_cost = self._calculator.calculate_token_costs(
            input_tokens,
            output_tokens,
            input_cost_per_1k_tokens,
            output_cost_per_1k_tokens,
        )
        return CostEstimate(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=estimated_cost,
        )
