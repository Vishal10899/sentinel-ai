"""Standalone Enterprise Pricing Engine.

Reads token pricing specs directly from the Enterprise Provider Registry.
Provider adapters do NOT contain pricing logic.
"""

from dataclasses import dataclass
from decimal import Decimal
from app.models_registry import model_registry


@dataclass(frozen=True, slots=True)
class ModelPricingSpec:
    """Pricing specification for a model."""

    provider_id: str
    model_id: str
    cost_per_1k_input_tokens: Decimal
    cost_per_1k_output_tokens: Decimal
    cost_per_1k_cached_tokens: Decimal
    cost_per_1k_reasoning_tokens: Decimal
    cost_per_image: Decimal
    cost_per_1k_embedding_tokens: Decimal

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "cost_per_1k_input_tokens": float(self.cost_per_1k_input_tokens),
            "cost_per_1k_output_tokens": float(self.cost_per_1k_output_tokens),
            "cost_per_1k_cached_tokens": float(self.cost_per_1k_cached_tokens),
            "cost_per_1k_reasoning_tokens": float(self.cost_per_1k_reasoning_tokens),
            "cost_per_image": float(self.cost_per_image),
            "cost_per_1k_embedding_tokens": float(self.cost_per_1k_embedding_tokens),
        }


@dataclass(frozen=True, slots=True)
class DetailedCostEstimate:
    """Detailed cost calculation breakdown."""

    provider_id: str
    model_id: str
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int
    reasoning_tokens: int
    prompt_cost_usd: Decimal
    completion_cost_usd: Decimal
    cached_cost_usd: Decimal
    reasoning_cost_usd: Decimal
    total_cost_usd: Decimal

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cached_tokens": self.cached_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "prompt_cost_usd": float(self.prompt_cost_usd),
            "completion_cost_usd": float(self.completion_cost_usd),
            "cached_cost_usd": float(self.cached_cost_usd),
            "reasoning_cost_usd": float(self.reasoning_cost_usd),
            "total_cost_usd": float(self.total_cost_usd),
        }


class PricingEngine:
    """Enterprise Pricing Engine enforcing zero duplicate pricing definitions."""

    def get_pricing_spec(self, provider_id: str, model_id: str) -> ModelPricingSpec:
        """Lookup model pricing spec from ModelRegistry."""
        m = model_registry.get_model(provider_id, model_id)
        return ModelPricingSpec(
            provider_id=m.provider_id,
            model_id=m.model_id,
            cost_per_1k_input_tokens=m.cost_per_1k_input_tokens,
            cost_per_1k_output_tokens=m.cost_per_1k_output_tokens,
            cost_per_1k_cached_tokens=m.cost_per_1k_cached_tokens,
            cost_per_1k_reasoning_tokens=m.cost_per_1k_reasoning_tokens,
            cost_per_image=m.cost_per_image,
            cost_per_1k_embedding_tokens=m.cost_per_1k_embedding_tokens,
        )

    def calculate_cost(
        self,
        provider_id: str,
        model_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
        reasoning_tokens: int = 0,
    ) -> DetailedCostEstimate:
        """Calculate exact token costs for input, completion, cached, and reasoning tokens (< 2ms)."""
        spec = self.get_pricing_spec(provider_id, model_id)

        prompt_cost = (Decimal(str(prompt_tokens)) / Decimal("1000")) * spec.cost_per_1k_input_tokens
        completion_cost = (Decimal(str(completion_tokens)) / Decimal("1000")) * spec.cost_per_1k_output_tokens
        cached_cost = (Decimal(str(cached_tokens)) / Decimal("1000")) * spec.cost_per_1k_cached_tokens
        reasoning_cost = (Decimal(str(reasoning_tokens)) / Decimal("1000")) * spec.cost_per_1k_reasoning_tokens

        total_cost = prompt_cost + completion_cost + cached_cost + reasoning_cost

        return DetailedCostEstimate(
            provider_id=provider_id,
            model_id=model_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cached_tokens=cached_tokens,
            reasoning_tokens=reasoning_tokens,
            prompt_cost_usd=prompt_cost.quantize(Decimal("0.000001")),
            completion_cost_usd=completion_cost.quantize(Decimal("0.000001")),
            cached_cost_usd=cached_cost.quantize(Decimal("0.000001")),
            reasoning_cost_usd=reasoning_cost.quantize(Decimal("0.000001")),
            total_cost_usd=total_cost.quantize(Decimal("0.000001")),
        )


pricing_engine = PricingEngine()
