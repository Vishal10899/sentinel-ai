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
    VISION = "vision"
    AUDIO = "audio"
    REASONING = "reasoning"
    FUNCTION_CALLING = "function_calling"
    IMAGE_GENERATION = "image_generation"


@dataclass(frozen=True, slots=True)
class ModelInfo:
    """Enterprise model metadata used by routing strategies and circuit breakers."""

    provider: str
    model_name: str
    cost_per_1k_tokens: float
    latency: float
    capabilities: frozenset[TaskCategory]
    priority: int
    category: str = "chat"
    context_window: int = 128000
    max_output_tokens: int = 4096
    quality_score: float = 80.0
    reasoning_score: float = 80.0
    speed_score: float = 80.0
    provider_status: str = "healthy"
    provider_failures: int = 0
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_audio: bool = False
    supports_function_calling: bool = True
    supports_embeddings: bool = True
    supports_image_generation: bool = False

    def supports(self, task_type: TaskCategory) -> bool:
        """Return whether this model advertises support for the requested task."""
        if task_type == TaskCategory.CHAT:
            if self.category.lower() in ["embedding", "rerank", "moderation", "image", "audio"]:
                return False
        return task_type in self.capabilities or self.category.lower() == task_type.value.lower()


@dataclass(frozen=True, slots=True)
class CandidateScore:
    """Scored candidate model details generated during routing evaluation."""

    provider: str
    model_name: str
    overall_score: float
    rank: int
    cost_per_1k_tokens: float
    latency: float
    quality_score: float
    reasoning_score: float
    status: str
    reason: str


@dataclass(frozen=True, slots=True)
class RoutingDecisionExplanation:
    """Human-readable and structured decision trace explaining model selection."""

    selected_provider: str
    selected_model: str
    strategy_used: str
    primary_reason: str
    ranked_candidates: tuple[CandidateScore, ...]
    failover_triggered: bool = False
    circuit_breaker_bypassed: tuple[str, ...] = ()
