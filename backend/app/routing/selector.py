"""Capability-based candidate selection for the routing engine."""

from collections.abc import Sequence

from app.routing.types import ModelInfo, TaskCategory


class ModelSelector:
    """Filter supplied model metadata before a strategy makes a selection."""

    def compatible_models(
        self,
        task_type: TaskCategory,
        available_providers: Sequence[ModelInfo],
    ) -> list[ModelInfo]:
        """Return only models that declare the requested task capability."""
        return [
            model for model in available_providers if model.supports(task_type)
        ]
