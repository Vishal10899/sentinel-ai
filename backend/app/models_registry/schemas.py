"""Immutable provider and model metadata schemas for the Enterprise Provider Registry."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderMetadata:
    """Static and dynamic metadata describing an enterprise AI provider."""

    provider_id: str
    provider_name: str
    enabled: bool = True
    status: str = "healthy"  # healthy, degraded, down, disabled
    provider_type: str = "cloud"  # cloud, local, hybrid, custom
    supported_regions: tuple[str, ...] = field(default_factory=lambda: ("us-east-1", "us-west-2", "eu-west-1"))
    available_models: tuple[str, ...] = field(default_factory=tuple)
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    default_model: str = ""
    priority: int = 10
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_json_mode: bool = True
    supports_function_calling: bool = True
    supports_image_input: bool = False
    supports_audio_input: bool = False
    supports_embeddings: bool = True
    supports_batch: bool = False
    supports_fine_tuning: bool = False
    supports_tool_calling: bool = True
    supports_reasoning: bool = False
    supports_long_context: bool = True
    max_context_window: int = 1_000_000
    max_output_tokens: int = 8192
    rate_limits: dict[str, int] = field(default_factory=lambda: {"rpm": 600, "tpm": 100000})
    concurrent_request_limits: int = 50
    timeout_defaults: float = 30.0
    retry_policy: dict[str, Any] = field(default_factory=lambda: {"max_retries": 2, "backoff_factor": 2.0})
    auth_type: str = "api_key"  # api_key, oauth2, mTLS, IAM
    health_status: str = "healthy"
    circuit_breaker_status: str = "closed"  # closed, open, half-open
    current_availability: float = 99.95  # Percentage SLA

    def __post_init__(self) -> None:
        if not self.provider_id or not self.provider_name:
            raise ValueError("Provider identifier cannot be empty")

    @property
    def provider(self) -> str:
        return self.provider_id

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "enabled": self.enabled,
            "status": self.status,
            "provider_type": self.provider_type,
            "supported_regions": list(self.supported_regions),
            "available_models": list(self.available_models),
            "capabilities": list(self.capabilities),
            "default_model": self.default_model,
            "priority": self.priority,
            "supports_streaming": self.supports_streaming,
            "supports_vision": self.supports_vision,
            "supports_json_mode": self.supports_json_mode,
            "supports_function_calling": self.supports_function_calling,
            "supports_image_input": self.supports_image_input,
            "supports_audio_input": self.supports_audio_input,
            "supports_embeddings": self.supports_embeddings,
            "supports_batch": self.supports_batch,
            "supports_fine_tuning": self.supports_fine_tuning,
            "supports_tool_calling": self.supports_tool_calling,
            "supports_reasoning": self.supports_reasoning,
            "supports_long_context": self.supports_long_context,
            "max_context_window": self.max_context_window,
            "max_output_tokens": self.max_output_tokens,
            "rate_limits": self.rate_limits,
            "concurrent_request_limits": self.concurrent_request_limits,
            "timeout_defaults": self.timeout_defaults,
            "retry_policy": self.retry_policy,
            "auth_type": self.auth_type,
            "health_status": self.health_status,
            "circuit_breaker_status": self.circuit_breaker_status,
            "current_availability": self.current_availability,
        }


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    """Enterprise metadata describing an AI model candidate in the Model Catalog."""

    provider_id: str
    provider_name: str
    model_id: str
    display_name: str
    capabilities: frozenset[str]
    cost_per_1k_input_tokens: Decimal
    cost_per_1k_output_tokens: Decimal
    average_latency_ms: int
    priority: int
    context_window: int
    category: str = "chat"
    max_output_tokens: int = 4096
    cost_per_1k_cached_tokens: Decimal = Decimal("0.00005")
    cost_per_1k_reasoning_tokens: Decimal = Decimal("0.0030")
    cost_per_image: Decimal = Decimal("0.0040")
    cost_per_1k_embedding_tokens: Decimal = Decimal("0.00002")
    release_version: str = "1.0.0"
    family: str = "general"
    supports_streaming: bool = True
    supports_function_calling: bool = True
    supports_vision: bool = False
    supports_audio: bool = False
    supports_reasoning: bool = False
    supports_coding: bool = True
    supports_math: bool = True
    json_reliability_score: float = 95.0
    function_calling_score: float = 92.0
    embedding_quality_score: float = 90.0
    reasoning_score: float = 80.0
    speed_score: float = 80.0
    quality_score: float = 80.0
    cost_score: float = 80.0
    popularity_score: float = 85.0
    recommended_use_cases: tuple[str, ...] = field(default_factory=lambda: ("general_chat", "coding", "summarization"))
    enabled: bool = True
    deprecated: bool = False
    stable: bool = True
    enterprise_approved: bool = True

    def __post_init__(self) -> None:
        if not self.provider_id or not self.provider_name or not self.model_id:
            raise ValueError("Provider and model name cannot be empty")
        if self.cost_per_1k_input_tokens < 0 or self.cost_per_1k_output_tokens < 0:
            raise ValueError("Model token costs cannot be negative")
        if self.average_latency_ms < 0:
            raise ValueError("Average latency cannot be negative")
        if self.context_window <= 0:
            raise ValueError("Context window must be positive")

    @property
    def provider(self) -> str:
        return self.provider_id

    @property
    def model_name(self) -> str:
        return self.model_id

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "model_id": self.model_id,
            "display_name": self.display_name,
            "capabilities": list(self.capabilities),
            "cost_per_1k_input_tokens": float(self.cost_per_1k_input_tokens),
            "cost_per_1k_output_tokens": float(self.cost_per_1k_output_tokens),
            "cost_per_1k_cached_tokens": float(self.cost_per_1k_cached_tokens),
            "cost_per_1k_reasoning_tokens": float(self.cost_per_1k_reasoning_tokens),
            "cost_per_image": float(self.cost_per_image),
            "cost_per_1k_embedding_tokens": float(self.cost_per_1k_embedding_tokens),
            "average_latency_ms": self.average_latency_ms,
            "priority": self.priority,
            "context_window": self.context_window,
            "category": self.category,
            "max_output_tokens": self.max_output_tokens,
            "release_version": self.release_version,
            "family": self.family,
            "supports_streaming": self.supports_streaming,
            "supports_function_calling": self.supports_function_calling,
            "supports_vision": self.supports_vision,
            "supports_audio": self.supports_audio,
            "supports_reasoning": self.supports_reasoning,
            "supports_coding": self.supports_coding,
            "supports_math": self.supports_math,
            "json_reliability_score": self.json_reliability_score,
            "function_calling_score": self.function_calling_score,
            "embedding_quality_score": self.embedding_quality_score,
            "reasoning_score": self.reasoning_score,
            "speed_score": self.speed_score,
            "quality_score": self.quality_score,
            "cost_score": self.cost_score,
            "popularity_score": self.popularity_score,
            "recommended_use_cases": list(self.recommended_use_cases),
            "enabled": self.enabled,
            "deprecated": self.deprecated,
            "stable": self.stable,
            "enterprise_approved": self.enterprise_approved,
        }
