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
        highest_cost = max((model.cost_per_1k_tokens for model in candidates), default=1.0) or 1.0
        highest_latency = max((model.latency for model in candidates), default=1.0) or 1.0

        return min(
            candidates,
            key=lambda model: (
                (model.cost_per_1k_tokens / highest_cost)
                + (model.latency / highest_latency),
                model.priority,
            ),
        )


class HighestQualityStrategy(RoutingStrategy):
    """Prefer the highest quality benchmark score, then lower latency and priority."""

    def select(self, candidates: Sequence[ModelInfo]) -> ModelInfo:
        return max(
            candidates,
            key=lambda model: (
                model.quality_score,
                -model.latency,
                -model.cost_per_1k_tokens,
                -model.priority,
            ),
        )


class ReasoningOptimizedStrategy(RoutingStrategy):
    """Prefer models with high reasoning score for complex analytical or coding tasks."""

    def select(self, candidates: Sequence[ModelInfo]) -> ModelInfo:
        return max(
            candidates,
            key=lambda model: (
                model.reasoning_score,
                model.quality_score,
                -model.latency,
                -model.priority,
            ),
        )


class VisionOptimizedStrategy(RoutingStrategy):
    """Prefer models that support vision modality with high quality scores."""

    def select(self, candidates: Sequence[ModelInfo]) -> ModelInfo:
        vision_candidates = [m for m in candidates if m.supports_vision]
        pool = vision_candidates if vision_candidates else candidates
        return max(
            pool,
            key=lambda model: (
                model.quality_score,
                -model.latency,
                -model.priority,
            ),
        )


class EmbeddingOptimizedStrategy(RoutingStrategy):
    """Prefer low latency and low cost models for high-throughput vector embedding generation."""

    def select(self, candidates: Sequence[ModelInfo]) -> ModelInfo:
        embedding_candidates = [m for m in candidates if m.category.lower() == "embedding" or m.supports_embeddings]
        pool = embedding_candidates if embedding_candidates else candidates
        return min(
            pool,
            key=lambda model: (
                model.cost_per_1k_tokens,
                model.latency,
                model.priority,
            ),
        )


class ImageGenerationOptimizedStrategy(RoutingStrategy):
    """Prefer models capable of image synthesis or high visual quality."""

    def select(self, candidates: Sequence[ModelInfo]) -> ModelInfo:
        image_candidates = [m for m in candidates if m.supports_image_generation or m.category.lower() == "image"]
        pool = image_candidates if image_candidates else candidates
        return max(
            pool,
            key=lambda model: (
                model.quality_score,
                -model.latency,
                -model.priority,
            ),
        )


class CustomWeightedStrategy(RoutingStrategy):
    """Evaluate candidates using configurable normalized weights for cost, latency, quality, and reasoning."""

    def __init__(
        self,
        cost_weight: float = 0.25,
        latency_weight: float = 0.25,
        quality_weight: float = 0.25,
        reasoning_weight: float = 0.25,
    ) -> None:
        self.cost_weight = cost_weight
        self.latency_weight = latency_weight
        self.quality_weight = quality_weight
        self.reasoning_weight = reasoning_weight

    def evaluate_score(self, model: ModelInfo, max_cost: float, max_lat: float) -> float:
        norm_cost = 1.0 - (model.cost_per_1k_tokens / max_cost) if max_cost > 0 else 1.0
        norm_lat = 1.0 - (model.latency / max_lat) if max_lat > 0 else 1.0
        norm_qual = (model.quality_score / 100.0)
        norm_reason = (model.reasoning_score / 100.0)

        score = (
            (norm_cost * self.cost_weight)
            + (norm_lat * self.latency_weight)
            + (norm_qual * self.quality_weight)
            + (norm_reason * self.reasoning_weight)
        )
        return round(score * 100, 2)

    def select(self, candidates: Sequence[ModelInfo]) -> ModelInfo:
        max_cost = max((m.cost_per_1k_tokens for m in candidates), default=1.0) or 1.0
        max_lat = max((m.latency for m in candidates), default=1.0) or 1.0

        return max(
            candidates,
            key=lambda model: (
                self.evaluate_score(model, max_cost, max_lat),
                -model.priority,
            ),
        )
