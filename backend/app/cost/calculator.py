"""Pure token-cost calculation with decimal precision."""

from decimal import Decimal


class CostCalculator:
    """Calculate estimated cost from token counts and a per-1,000-token price."""

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cost_per_1k_tokens: Decimal | float | str,
    ) -> Decimal:
        """Return the total estimated cost using one price for all supplied tokens."""
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("Token counts cannot be negative")

        unit_cost = Decimal(str(cost_per_1k_tokens))
        if unit_cost < 0:
            raise ValueError("Cost per 1K tokens cannot be negative")

        total_tokens = Decimal(input_tokens + output_tokens)
        return (total_tokens / Decimal("1000")) * unit_cost

    def calculate_token_costs(
        self,
        input_tokens: int,
        output_tokens: int,
        input_cost_per_1k_tokens: Decimal | float | str,
        output_cost_per_1k_tokens: Decimal | float | str,
    ) -> Decimal:
        """Return a cost using the distinct input and output prices of a model."""
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("Token counts cannot be negative")

        input_price = Decimal(str(input_cost_per_1k_tokens))
        output_price = Decimal(str(output_cost_per_1k_tokens))
        if input_price < 0 or output_price < 0:
            raise ValueError("Cost per 1K tokens cannot be negative")

        return (
            (Decimal(input_tokens) / Decimal("1000")) * input_price
            + (Decimal(output_tokens) / Decimal("1000")) * output_price
        )
