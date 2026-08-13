"""Unified Capability Matrix Engine.

Single source of truth for model capability profiles consumed uniformly across
Routing, Execution Orchestration, UI, and Analytics.
"""

from dataclasses import dataclass, field
from app.models_registry.schemas import ModelMetadata


@dataclass(frozen=True, slots=True)
class CapabilityProfile:
    """Standardized model capability profile."""

    model_id: str
    provider_id: str
    category: str
    supports_chat: bool
    supports_coding: bool
    supports_reasoning: bool
    supports_math: bool
    supports_vision: bool
    supports_audio: bool
    supports_json: bool
    supports_tools: bool
    supports_embeddings: bool
    supports_long_context: bool
    context_window: int
    max_output_tokens: int
    quality_score: float
    reasoning_score: float
    latency_ms: int
    recommended_tasks: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "provider_id": self.provider_id,
            "category": self.category,
            "supports_chat": self.supports_chat,
            "supports_coding": self.supports_coding,
            "supports_reasoning": self.supports_reasoning,
            "supports_math": self.supports_math,
            "supports_vision": self.supports_vision,
            "supports_audio": self.supports_audio,
            "supports_json": self.supports_json,
            "supports_tools": self.supports_tools,
            "supports_embeddings": self.supports_embeddings,
            "supports_long_context": self.supports_long_context,
            "context_window": self.context_window,
            "max_output_tokens": self.max_output_tokens,
            "quality_score": self.quality_score,
            "reasoning_score": self.reasoning_score,
            "latency_ms": self.latency_ms,
            "recommended_tasks": list(self.recommended_tasks),
        }


class CapabilityMatrixEngine:
    """Generate and query unified model capability matrices."""

    def build_profile(self, model: ModelMetadata) -> CapabilityProfile:
        """Construct capability profile from ModelMetadata."""
        caps = model.capabilities
        return CapabilityProfile(
            model_id=model.model_id,
            provider_id=model.provider_id,
            category=model.category,
            supports_chat="chat" in caps or model.category.lower() == "chat",
            supports_coding=model.supports_coding or "code_generation" in caps,
            supports_reasoning=model.supports_reasoning or "reasoning" in caps,
            supports_math=model.supports_math,
            supports_vision=model.supports_vision or "vision" in caps,
            supports_audio=model.supports_audio or "audio" in caps,
            supports_json=model.json_reliability_score >= 80.0,
            supports_tools=model.supports_function_calling or "function_calling" in caps,
            supports_embeddings=model.category.lower() == "embedding" or "embedding" in caps,
            supports_long_context=model.context_window >= 128_000,
            context_window=model.context_window,
            max_output_tokens=model.max_output_tokens,
            quality_score=model.quality_score,
            reasoning_score=model.reasoning_score,
            latency_ms=model.average_latency_ms,
            recommended_tasks=model.recommended_use_cases,
        )

    def generate_matrix(self, models: list[ModelMetadata]) -> dict[str, CapabilityProfile]:
        """Generate lookup map of model_id -> CapabilityProfile."""
        return {f"{m.provider_id}/{m.model_id}": self.build_profile(m) for m in models}


capability_matrix_engine = CapabilityMatrixEngine()
