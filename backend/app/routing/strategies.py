"""Interchangeable, metadata-only routing strategies."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.routing.types import ModelInfo


class RoutingStrategy(ABC):
    """Contract for selecting one model from already compatible candidates."""

    @abstractmethod
    def select(self, candidates: Sequence[ModelInfo]) -> ModelInfo:
        """Choose one candidate using strategy-specific metadata rules."""


class CheapestStrategy(RoutingStrategy):
    """Prefer the lowest estimated token cost, then latency and priority."""

    def select(self, candidates: Sequence[ModelInfo]) -> ModelInfo:
        """Select deterministically from compatible model metadata."""
        return min(
            candidates,
            key=lambda model: (
                model.cost_per_1k_tokens,
                model.latency,
                model.priority,
            ),
        )


class FastestStrategy(RoutingStrategy):
    """Prefer the lowest estimated latency, then cost and priority."""

    def select(self, candidates: Sequence[ModelInfo]) -> ModelInfo:
        """Select deterministically from compatible model metadata."""
        return min(
            candidates,
            key=lambda model: (
                model.latency,
                model.cost_per_1k_tokens,
                model.priority,
            ),
        )


class BalancedStrategy(RoutingStrategy):
    """Balance normalized cost and latency, using priority as a deterministic tie-breaker."""

    def select(self, candidates: Sequence[ModelInfo]) -> ModelInfo:
        """Select a balanced candidate using only supplied static metadata."""
        highest_cost = max(model.cost_per_1k_tokens for model in candidates) or 1
        highest_latency = max(model.latency for model in candidates) or 1

        return min(
            candidates,
            key=lambda model: (
                (model.cost_per_1k_tokens / highest_cost)
                + (model.latency / highest_latency),
                model.priority,
            ),
        )
