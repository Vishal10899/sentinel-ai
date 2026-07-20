"""Immutable provider and model metadata schemas for infrastructure consumers."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ProviderMetadata:
    """Static metadata describing a provider available to the application."""

    provider_id: str
    provider_name: str
    enabled: bool = True

    def __post_init__(self) -> None:
        """Reject invalid provider identifiers at registry construction time."""
        if not self.provider_id or not self.provider_name:
            raise ValueError("Provider identifier cannot be empty")

    @property
    def provider(self) -> str:
        """Retain the original provider-name accessor for existing consumers."""
        return self.provider_id


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    """Static model metadata consumed by routing and cost callers."""

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
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate infrastructure metadata without applying routing policy."""
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
        """Provide the legacy provider accessor used by registry consumers."""
        return self.provider_id

    @property
    def model_name(self) -> str:
        """Provide the legacy model-name accessor used by registry consumers."""
        return self.model_id
