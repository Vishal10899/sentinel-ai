"""Routing-domain types that do not depend on provider SDKs or API layers."""

from dataclasses import dataclass
from enum import Enum

class TaskCategory(str, Enum):
    """Supported task categories for model-capability matching."""

    CHAT = "chat"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"
    CODE_GENERATION = "code_generation"


@dataclass(frozen=True, slots=True)
class ModelInfo:
    """Static model metadata used by routing strategies without calling a provider."""

    provider: str
    model_name: str
    cost_per_1k_tokens: float
    latency: float
    capabilities: frozenset[TaskCategory]
    priority: int

    def supports(self, task_type: TaskCategory) -> bool:
        """Return whether this model advertises support for the requested task."""
        return task_type in self.capabilities
