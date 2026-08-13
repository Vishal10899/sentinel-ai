"""Enterprise Trace & Observability Engine.

Assigns unique trace_id and parent_span_id, records hierarchical execution spans,
and captures request metadata with < 3ms processing overhead.
"""

from dataclasses import asdict
import time
from typing import Any
from uuid import uuid4

from app.audit.engine import audit_engine
from app.observability.models import ExecutionSpan, RequestReplaySnapshot, TimelineStage, TraceRecord
from app.observability.repository import ObservabilityRepository, observability_repository


class TraceContext:
    """Active distributed trace context manager tracking hierarchical spans & execution lifecycle."""

    def __init__(
        self,
        trace_id: str,
        conversation_id: str,
        workspace_id: str,
        user_id: str,
        provider_id: str,
        model_id: str,
        prompt: str,
        repository: ObservabilityRepository,
    ) -> None:
        self.trace_id = trace_id
        self.root_span_id = f"span-root-{uuid4().hex[:8]}"
        self.correlation_id = f"corr-{trace_id[:8]}"
        self.conversation_id = conversation_id
        self.workspace_id = workspace_id
        self.user_id = user_id
        self.provider_id = provider_id
        self.model_id = model_id
        self.prompt = prompt
        self.repository = repository

        self.start_time = time.time()
        self.stages: list[TimelineStage] = []
        self.spans: list[ExecutionSpan] = []
        self._active_stage: TimelineStage | None = None

        self.prompt_tokens = max(len(prompt) // 4, 1)
        self.completion_tokens = 0
        self.tokens = self.prompt_tokens
        self.cost_usd = 0.0
        self.retry_count = 0
        self.failover_count = 0
        self.bypassed_providers: list[str] = []

        self.guardrail_action = "ALLOW"
        self.policy_action = "ALLOW"
        self.policy_id: str | None = None
        self.cache_hit = False
        self.response = ""
        self.status = "SUCCESS"
        self.status_code = 200

    def start_span(self, span_name: str, parent_span_id: str | None = None, metadata: dict[str, Any] | None = None) -> tuple[str, float]:
        """Start a hierarchical execution span."""
        span_id = f"span-{uuid4().hex[:8]}"
        p_id = parent_span_id or self.root_span_id
        start_t = time.time()
        return span_id, start_t

    def record_span(self, span_name: str, start_time: float, parent_span_id: str | None = None, status: str = "SUCCESS", metadata: dict[str, Any] | None = None) -> ExecutionSpan:
        """Record a completed execution span."""
        end_t = time.time()
        dur_ms = round((end_t - start_time) * 1000, 2)
        span = ExecutionSpan(
            span_id=f"span-{uuid4().hex[:8]}",
            parent_span_id=parent_span_id or self.root_span_id,
            span_name=span_name,
            started_at=start_time,
            ended_at=end_t,
            duration_ms=dur_ms,
            status=status,
            metadata=metadata or {},
        )
        self.spans.append(span)
        return span

    def start_stage(self, stage_name: str, metadata: dict[str, Any] | None = None) -> TimelineStage:
        """Start tracking a new execution stage."""
        if self._active_stage and self._active_stage.ended_at is None:
            self._active_stage.complete()
        stage = TimelineStage(stage_name=stage_name, started_at=time.time(), metadata=metadata or {})
        self.stages.append(stage)
        self._active_stage = stage
        return stage

    def end_stage(self, stage_name: str, status: str = "SUCCESS", metadata: dict[str, Any] | None = None) -> None:
        """Complete an active stage."""
        for s in reversed(self.stages):
            if s.stage_name == stage_name and s.ended_at is None:
                s.complete(status=status, metadata=metadata)
                break

    def finish(
        self,
        status: str = "SUCCESS",
        response: str = "",
        tokens: int = 0,
        cost_usd: float = 0.0,
        status_code: int = 200,
        retry_count: int = 0,
        failover_count: int = 0,
        bypassed_providers: list[str] | None = None,
    ) -> TraceRecord:
        """Finalize and persist trace record (< 3ms)."""
        if self._active_stage and self._active_stage.ended_at is None:
            self._active_stage.complete()

        total_latency = round((time.time() - self.start_time) * 1000, 2)
        self.status = status
        self.response = response
        self.status_code = status_code
        self.retry_count = retry_count
        self.failover_count = failover_count
        if bypassed_providers:
            self.bypassed_providers = bypassed_providers

        if tokens > 0:
            self.completion_tokens = max(tokens - self.prompt_tokens, 0)
            self.tokens = tokens
        else:
            self.completion_tokens = max(len(response) // 4, 1)
            self.tokens = self.prompt_tokens + self.completion_tokens

        self.cost_usd = cost_usd

        record = TraceRecord(
            trace_id=self.trace_id,
            correlation_id=self.correlation_id,
            conversation_id=self.conversation_id,
            workspace_id=self.workspace_id,
            user_id=self.user_id,
            provider_id=self.provider_id,
            model_id=self.model_id,
            prompt=self.prompt,
            response=response,
            tokens=self.tokens,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            cost_usd=cost_usd,
            total_latency_ms=total_latency,
            status=status,
            status_code=status_code,
            retry_count=retry_count,
            failover_count=failover_count,
            bypassed_providers=self.bypassed_providers,
            timeline_stages=self.stages,
            spans=self.spans,
            guardrail_action=self.guardrail_action,
            policy_action=self.policy_action,
            policy_id=self.policy_id,
            cache_hit=self.cache_hit,
            created_at=self.start_time,
        )
        self.repository.save_trace(record)
        return record


class TraceEngine:
    """Enterprise Trace & Observability Orchestrator."""

    def __init__(self, repository: ObservabilityRepository | None = None) -> None:
        self.repository = repository or observability_repository

    def create_trace(
        self,
        conversation_id: str = "",
        workspace_id: str = "default",
        user_id: str = "default_user",
        provider_id: str = "gemini",
        model_id: str = "gemini-2.0-flash",
        prompt: str = "",
    ) -> TraceContext:
        """Start a new distributed trace context."""
        trace_id = str(uuid4())
        return TraceContext(
            trace_id=trace_id,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            user_id=user_id,
            provider_id=provider_id,
            model_id=model_id,
            prompt=prompt,
            repository=self.repository,
        )

    def generate_replay(self, trace_id: str, requesting_user_id: str = "admin") -> RequestReplaySnapshot | None:
        """Generate a read-only Request Replay Snapshot for a trace ID and log audit event."""
        trace = self.repository.get_trace(trace_id)
        if not trace:
            return None

        audit_engine.record_event(
            action="REQUEST_REPLAY_VIEWED",
            resource=f"traces/{trace_id}",
            user_id=requesting_user_id,
            workspace_id=trace.workspace_id,
            severity="INFO",
        )

        return RequestReplaySnapshot(
            trace_id=trace.trace_id,
            timestamp=trace.created_at,
            workspace_id=trace.workspace_id,
            user_id=trace.user_id,
            conversation_id=trace.conversation_id,
            provider_id=trace.provider_id,
            model_id=trace.model_id,
            prompt=trace.prompt,
            response=trace.response,
            tokens=trace.tokens,
            cost_usd=trace.cost_usd,
            total_latency_ms=trace.total_latency_ms,
            status=trace.status,
            policy_decision=trace.policy_action,
            guardrail_decision=trace.guardrail_action,
            cache_hit=trace.cache_hit,
            timeline_stages=[s.to_dict() for s in trace.timeline_stages],
        )


trace_engine = TraceEngine()
