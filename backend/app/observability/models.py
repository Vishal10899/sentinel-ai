"""Observability and Tracing domain models."""

from dataclasses import dataclass, field
import datetime
import time
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderHealthStatus:
    """Provider health telemetry status record."""

    provider_id: str
    provider_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    success_rate: float
    status: str = "HEALTHY"
    last_successful_request_at: float | None = None

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "avg_latency_ms": self.avg_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "success_rate": self.success_rate,
            "status": self.status,
            "last_successful_request_at": self.last_successful_request_at,
        }


@dataclass(frozen=True, slots=True)
class ExecutionSpan:
    """Hierarchical execution span representing a sub-operation within a trace."""

    span_id: str
    parent_span_id: str | None
    span_name: str
    started_at: float
    ended_at: float
    duration_ms: float
    status: str = "SUCCESS"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "span_name": self.span_name,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "metadata": self.metadata,
        }


@dataclass
class TimelineStage:
    """Execution timeline stage for trace visualizations."""

    stage_name: str
    started_at: float
    ended_at: float | None = None
    duration_ms: float = 0.0
    status: str = "RUNNING"
    metadata: dict[str, Any] = field(default_factory=dict)

    def complete(self, status: str = "SUCCESS", metadata: dict[str, Any] | None = None) -> None:
        """Mark stage completed."""
        self.ended_at = time.time()
        self.duration_ms = round((self.ended_at - self.started_at) * 1000, 2)
        self.status = status
        if metadata:
            self.metadata.update(metadata)

    def to_dict(self) -> dict:
        return {
            "stage_name": self.stage_name,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "metadata": self.metadata,
        }


@dataclass
class TraceRecord:
    """Complete distributed trace record covering an entire LLM Control Plane request lifecycle."""

    trace_id: str
    correlation_id: str
    conversation_id: str
    workspace_id: str
    user_id: str
    provider_id: str
    model_id: str
    prompt: str
    response: str
    tokens: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    status: str = "SUCCESS"
    status_code: int = 200
    retry_count: int = 0
    failover_count: int = 0
    bypassed_providers: list[str] = field(default_factory=list)
    timeline_stages: list[TimelineStage] = field(default_factory=list)
    spans: list[ExecutionSpan] = field(default_factory=list)
    guardrail_action: str = "ALLOW"
    policy_action: str = "ALLOW"
    policy_id: str | None = None
    cache_hit: bool = False
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "conversation_id": self.conversation_id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "prompt": self.prompt,
            "response": self.response,
            "tokens": self.tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_usd": self.cost_usd,
            "total_latency_ms": self.total_latency_ms,
            "status": self.status,
            "status_code": self.status_code,
            "retry_count": self.retry_count,
            "failover_count": self.failover_count,
            "bypassed_providers": self.bypassed_providers,
            "timeline_stages": [s.to_dict() for s in self.timeline_stages],
            "spans": [span.to_dict() for span in self.spans],
            "guardrail_action": self.guardrail_action,
            "policy_action": self.policy_action,
            "policy_id": self.policy_id,
            "cache_hit": self.cache_hit,
            "created_at": datetime.datetime.fromtimestamp(self.created_at, tz=datetime.timezone.utc).isoformat(),
        }


@dataclass(frozen=True, slots=True)
class RequestReplaySnapshot:
    """Read-only Request Replay Snapshot."""

    trace_id: str
    timestamp: float
    workspace_id: str
    user_id: str
    conversation_id: str
    provider_id: str
    model_id: str
    prompt: str
    response: str
    tokens: int
    cost_usd: float
    total_latency_ms: float
    status: str
    policy_decision: str
    guardrail_decision: str
    cache_hit: bool
    timeline_stages: list[dict[str, Any]]
