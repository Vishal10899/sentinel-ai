"""Enterprise Reliability Platform Domain Models."""

from dataclasses import dataclass, field
import datetime
from enum import Enum
from typing import Any
import uuid


class CircuitState(str, Enum):
    """Circuit Breaker Operational States."""

    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Trip state (diverting/blocking traffic)
    HALF_OPEN = "HALF_OPEN"  # Recovery testing trial state


class HealthProbeStatusEnum(str, Enum):
    """Provider Health Probe Statuses."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    OFFLINE = "OFFLINE"


@dataclass
class CircuitBreakerRecord:
    """Circuit Breaker configuration & telemetry record per provider/model."""

    provider_id: str
    model_id: str = "all"
    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    failure_threshold: int = 3
    recovery_timeout_seconds: float = 30.0
    half_open_trial_threshold: int = 2
    successful_trials: int = 0
    total_trips: int = 0
    last_failure_at: float | None = None
    last_state_change_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "state": self.state.value,
            "consecutive_failures": self.consecutive_failures,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_seconds": self.recovery_timeout_seconds,
            "successful_trials": self.successful_trials,
            "total_trips": self.total_trips,
            "last_failure_at": self.last_failure_at,
            "last_state_change_at": self.last_state_change_at,
        }


@dataclass(frozen=True, slots=True)
class RetryDecision:
    """Decision output produced by the Advanced Retry Engine."""

    should_retry: bool
    attempt: int
    wait_seconds: float
    reason: str
    is_transient: bool

    def to_dict(self) -> dict:
        return {
            "should_retry": self.should_retry,
            "attempt": self.attempt,
            "wait_seconds": self.wait_seconds,
            "reason": self.reason,
            "is_transient": self.is_transient,
        }


@dataclass(frozen=True, slots=True)
class TimeoutDecision:
    """Decision output produced by the Adaptive Timeout Engine."""

    provider_id: str
    model_id: str
    task_category: str
    hard_timeout_seconds: float
    soft_timeout_seconds: float
    reason: str

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "task_category": self.task_category,
            "hard_timeout_seconds": self.hard_timeout_seconds,
            "soft_timeout_seconds": self.soft_timeout_seconds,
            "reason": self.reason,
        }


@dataclass
class HealthProbeRecord:
    """Provider Health Probe Telemetry Record."""

    provider_id: str
    status: HealthProbeStatusEnum
    latency_ms: float
    last_checked_at: str
    error_message: str | None = None

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "last_checked_at": self.last_checked_at,
            "error_message": self.error_message,
        }
