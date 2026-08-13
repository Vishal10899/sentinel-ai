"""Production-Grade Circuit Breaker Engine.

Enforces provider/model state checks (CLOSED, OPEN, HALF_OPEN) in < 0.1 ms.
Manages failure thresholds, recovery timeouts, half-open trial transitions, and admin resets.
"""

import datetime
import time
from typing import Any

from app.reliability.models import CircuitBreakerRecord, CircuitState


class CircuitBreakerEngine:
    """Enterprise Circuit Breaker Engine (< 0.1 ms check state overhead)."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout_seconds: float = 30.0) -> None:
        self.default_failure_threshold = failure_threshold
        self.default_recovery_timeout = recovery_timeout_seconds
        self._breakers: dict[tuple[str, str], CircuitBreakerRecord] = {}

    def _get_key(self, provider_id: str, model_id: str | None = None) -> tuple[str, str]:
        return (provider_id.lower(), (model_id or "all").lower())

    def get_breaker(self, provider_id: str, model_id: str | None = None) -> CircuitBreakerRecord:
        """Get or initialize CircuitBreakerRecord."""
        key = self._get_key(provider_id, model_id)
        if key not in self._breakers:
            self._breakers[key] = CircuitBreakerRecord(
                provider_id=provider_id.lower(),
                model_id=(model_id or "all").lower(),
                failure_threshold=self.default_failure_threshold,
                recovery_timeout_seconds=self.default_recovery_timeout,
            )
        return self._breakers[key]

    def check_state(self, provider_id: str, model_id: str | None = None) -> CircuitState:
        """Check circuit breaker state in < 0.1 ms."""
        b = self.get_breaker(provider_id, model_id)

        # Check if OPEN state has expired recovery timeout
        if b.state == CircuitState.OPEN and b.last_failure_at:
            elapsed = time.time() - b.last_failure_at
            if elapsed >= b.recovery_timeout_seconds:
                b.state = CircuitState.HALF_OPEN
                b.successful_trials = 0
                b.last_state_change_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return b.state

    def record_success(self, provider_id: str, model_id: str | None = None) -> CircuitState:
        """Record successful call and manage HALF_OPEN trial recovery."""
        b = self.get_breaker(provider_id, model_id)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if b.state == CircuitState.HALF_OPEN:
            b.successful_trials += 1
            if b.successful_trials >= b.half_open_trial_threshold:
                b.state = CircuitState.CLOSED
                b.consecutive_failures = 0
                b.successful_trials = 0
                b.last_state_change_at = now
        elif b.state == CircuitState.CLOSED:
            b.consecutive_failures = 0

        return b.state

    def record_failure(self, provider_id: str, model_id: str | None = None) -> CircuitState:
        """Record failure and trip circuit breaker to OPEN if threshold exceeded."""
        b = self.get_breaker(provider_id, model_id)
        now_ts = time.time()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        b.consecutive_failures += 1
        b.last_failure_at = now_ts

        if b.state == CircuitState.HALF_OPEN or b.consecutive_failures >= b.failure_threshold:
            b.state = CircuitState.OPEN
            b.total_trips += 1
            b.last_state_change_at = now_iso

        return b.state

    def reset_circuit(self, provider_id: str, model_id: str | None = None) -> CircuitBreakerRecord:
        """Manually reset circuit breaker to CLOSED."""
        b = self.get_breaker(provider_id, model_id)
        b.state = CircuitState.CLOSED
        b.consecutive_failures = 0
        b.successful_trials = 0
        b.last_state_change_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return b

    def list_breakers(self) -> list[CircuitBreakerRecord]:
        """List all circuit breaker records."""
        return list(self._breakers.values())


circuit_breaker_engine = CircuitBreakerEngine()
