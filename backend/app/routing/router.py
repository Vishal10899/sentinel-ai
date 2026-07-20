"""High-level routing facade that composes selection and strategy policies."""

from collections.abc import Sequence

from app.routing.selector import ModelSelector
from app.routing.strategies import BalancedStrategy, RoutingStrategy
from app.routing.types import ModelInfo, TaskCategory


class IntelligentRouter:
    """Choose a provider from caller-supplied model metadata without performing AI work."""

    def __init__(
        self,
        strategy: RoutingStrategy | None = None,
        selector: ModelSelector | None = None,
    ) -> None:
        # Balanced selection is the default policy; callers may inject another strategy.
        self._strategy = strategy or BalancedStrategy()
        self._selector = selector or ModelSelector()

    def select_model(
        self,
        task_type: TaskCategory,
        available_providers: Sequence[ModelInfo],
    ) -> ModelInfo:
        """Select one compatible model for a task using the configured strategy."""
        candidates = self._selector.compatible_models(task_type, available_providers)
        if not candidates:
            raise ValueError(f"No provider supports task category '{task_type}'")

        return self._strategy.select(candidates)

    def select_provider(
        self,
        task_type: TaskCategory,
        available_providers: Sequence[ModelInfo],
    ) -> str:
        """Return the selected provider identifier for the requested task."""
        return self.select_model(task_type, available_providers).provider
