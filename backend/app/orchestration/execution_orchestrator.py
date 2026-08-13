"""Enterprise Execution Orchestrator.

Converts routing decisions into real LLM provider executions with request validation,
timeout management, transient retry policies, automatic failover, and response normalization.
"""

import asyncio
from dataclasses import dataclass, field
from decimal import Decimal
import logging
import time
import uuid

from app.audit.engine import audit_engine
from app.cost import CostCalculator
from app.observability.repository import observability_repository
from app.orchestration.exceptions import (
    SentinelAuthenticationError,
    SentinelEnterpriseError,
    SentinelExecutionOrchestrationError,
    SentinelInvalidRequestError,
    SentinelProviderTimeoutError,
    SentinelProviderUnavailableError,
    SentinelRateLimitError,
)
from app.providers.manager import provider_manager

logger = logging.getLogger("sentinel.orchestrator")


@dataclass
class ExecutionContext:
    """Execution context containing correlation IDs and execution state tracking."""

    request_id: str = field(default_factory=lambda: f"req-{uuid.uuid4().hex[:12]}")
    correlation_id: str = field(default_factory=lambda: f"corr-{uuid.uuid4().hex[:12]}")
    user_id: str = "default_user"
    workspace_id: str = "default"
    timeout_seconds: float = 120.0
    max_retries: int = 2
    retry_count: int = 0
    failover_count: int = 0
    bypassed_providers: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class NormalizedExecutionResponse:
    """Unified normalized response returned by the Execution Orchestrator."""

    request_id: str
    correlation_id: str
    provider: str
    model: str
    content: str
    usage: dict[str, int]
    latency_ms: float
    finish_reason: str
    estimated_cost_usd: float
    execution_time_ms: float
    retry_count: int
    failover_count: int
    bypassed_providers: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "provider": self.provider,
            "model": self.model,
            "content": self.content,
            "usage": self.usage,
            "latency_ms": self.latency_ms,
            "finish_reason": self.finish_reason,
            "estimated_cost_usd": self.estimated_cost_usd,
            "execution_time_ms": self.execution_time_ms,
            "retry_count": self.retry_count,
            "failover_count": self.failover_count,
            "bypassed_providers": list(self.bypassed_providers),
        }


class ExecutionOrchestrator:
    """Production-grade Enterprise AI Execution Orchestrator."""

    TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(self) -> None:
        self.cost_calculator = CostCalculator()

    def _is_transient_error(self, exc: Exception) -> bool:
        """Determine if an exception is transient and eligible for retry."""
        if isinstance(exc, (SentinelRateLimitError, SentinelProviderTimeoutError, SentinelProviderUnavailableError, TimeoutError, asyncio.TimeoutError, ConnectionError)):
            return True
        if isinstance(exc, SentinelEnterpriseError):
            return exc.status_code in self.TRANSIENT_STATUS_CODES
        return False

    def _translate_exception(self, exc: Exception, provider_id: str) -> SentinelEnterpriseError:
        """Translate raw provider exceptions into Sentinel enterprise exceptions."""
        if isinstance(exc, SentinelEnterpriseError):
            return exc

        msg = str(exc)
        msg_lower = msg.lower()

        if "401" in msg or "403" in msg or "auth" in msg_lower or "api_key" in msg_lower or "unauthorized" in msg_lower:
            return SentinelAuthenticationError(f"Authentication failed for provider '{provider_id}': {msg}")
        if "429" in msg or "rate limit" in msg_lower or "quota" in msg_lower:
            return SentinelRateLimitError(f"Rate limit exceeded for provider '{provider_id}': {msg}")
        if "timeout" in msg_lower or "timed out" in msg_lower:
            return SentinelProviderTimeoutError(f"Execution timed out for provider '{provider_id}': {msg}")
        if "500" in msg or "502" in msg or "503" in msg or "unavailable" in msg_lower:
            return SentinelProviderUnavailableError(f"Provider '{provider_id}' is unavailable: {msg}")

        return SentinelProviderUnavailableError(f"Provider '{provider_id}' execution failure: {msg}")

    async def _invoke_provider_with_retry(
        self,
        provider_id: str,
        model_id: str,
        prompt: str,
        system_prompt: str,
        ctx: ExecutionContext,
    ) -> tuple[str, float]:
        """Invoke provider adapter with exponential backoff retry for transient failures."""
        provider_adapter = provider_manager.get(provider_id)
        if not provider_adapter:
            raise SentinelInvalidRequestError(f"Provider '{provider_id}' is not registered in ProviderManager.")

        last_exc: Exception | None = None
        attempt = 0

        while attempt <= ctx.max_retries:
            try:
                t0 = time.perf_counter()

                # Execute with timeout management
                response_text = await asyncio.wait_for(
                    provider_adapter.generate(prompt, system_prompt=system_prompt, model=model_id),
                    timeout=ctx.timeout_seconds,
                )
                t1 = time.perf_counter()
                latency_ms = round((t1 - t0) * 1000, 2)
                return response_text, latency_ms

            except Exception as raw_exc:
                translated_exc = self._translate_exception(raw_exc, provider_id)
                last_exc = translated_exc

                if not self._is_transient_error(translated_exc) or attempt >= ctx.max_retries:
                    raise translated_exc

                ctx.retry_count += 1
                attempt += 1
                backoff_delay = 0.05 * (2 ** (attempt - 1))
                logger.warning(
                    f"[Orchestrator] Transient error on {provider_id}/{model_id} (Attempt {attempt}/{ctx.max_retries}). "
                    f"Retrying in {backoff_delay}s... Error: {translated_exc.message}"
                )
                await asyncio.sleep(backoff_delay)

        raise last_exc or SentinelProviderUnavailableError(f"Execution failed for provider '{provider_id}'.")

    async def execute(
        self,
        prompt: str,
        routing_decision: any,
        system_prompt: str = "",
        context: ExecutionContext | None = None,
    ) -> NormalizedExecutionResponse:
        """Execute request against selected candidate with failover and response normalization."""
        t_start = time.perf_counter()
        ctx = context or ExecutionContext()

        # Step 1: Request Validation
        text = prompt.strip()
        if not text:
            raise SentinelInvalidRequestError("Prompt input cannot be empty.")

        # Resolve candidate pool from routing decision
        primary_provider = getattr(routing_decision, "selected_provider", "gemini")
        primary_model = getattr(routing_decision, "selected_model", "gemini-2.0-flash")

        candidates_pool = []
        ranked_cands = getattr(routing_decision, "ranked_candidates", ())
        if ranked_cands:
            for c in ranked_cands:
                prov = getattr(c, "provider_id", getattr(c, "provider", "gemini"))
                mod = getattr(c, "model_id", getattr(c, "model_name", "gemini-2.0-flash"))
                if provider_manager.is_active(prov):
                    candidates_pool.append((prov, mod))

        if not candidates_pool and provider_manager.is_active(primary_provider):
            candidates_pool = [(primary_provider, primary_model)]

        if not candidates_pool:
            # Fall back to any active provider registered in provider_manager
            for p_name in provider_manager.provider_names():
                if provider_manager.is_active(p_name):
                    cfg = provider_manager.get_config(p_name)
                    candidates_pool.append((p_name, cfg.get("default_model") or "default"))
                    break

        # Audit & Observability Event: Execution Start
        logger.info(f"[Orchestrator] Execution Started | RequestID: {ctx.request_id} | Primary: {primary_provider}/{primary_model}")

        # Step 2: Provider Invocation with Failover Hierarchy
        last_failover_exc: Exception | None = None

        for idx, (prov_id, mod_id) in enumerate(candidates_pool):
            try:
                content, latency_ms = await self._invoke_provider_with_retry(
                    provider_id=prov_id,
                    model_id=mod_id,
                    prompt=text,
                    system_prompt=system_prompt,
                    ctx=ctx,
                )

                # Token usage & cost estimation
                prompt_tokens = max(len(text) // 4, 1)
                completion_tokens = max(len(content) // 4, 1)
                total_tokens = prompt_tokens + completion_tokens

                est_cost = float(
                    self.cost_calculator.calculate_token_costs(
                        prompt_tokens, completion_tokens, Decimal("0.0003"), Decimal("0.0003")
                    )
                )

                t_end = time.perf_counter()
                exec_time_ms = round((t_end - t_start) * 1000, 2)

                # Record Success Audit Event
                audit_engine.record_event(
                    action="EXECUTION_ORCHESTRATED_SUCCESS",
                    resource=f"models/{prov_id}/{mod_id}",
                    user_id=ctx.user_id,
                    workspace_id=ctx.workspace_id,
                    new_value=f"ReqID: {ctx.request_id} | Retries: {ctx.retry_count} | Failovers: {ctx.failover_count}",
                )

                return NormalizedExecutionResponse(
                    request_id=ctx.request_id,
                    correlation_id=ctx.correlation_id,
                    provider=prov_id,
                    model=mod_id,
                    content=content,
                    usage={
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                    },
                    latency_ms=latency_ms,
                    finish_reason="stop",
                    estimated_cost_usd=est_cost,
                    execution_time_ms=exec_time_ms,
                    retry_count=ctx.retry_count,
                    failover_count=ctx.failover_count,
                    bypassed_providers=tuple(ctx.bypassed_providers),
                )

            except SentinelEnterpriseError as exc:
                last_failover_exc = exc
                reason_msg = f"{prov_id}/{mod_id} failed ({exc.message})"
                ctx.bypassed_providers.append(reason_msg)
                ctx.failover_count += 1
                logger.warning(f"[Orchestrator] Failover triggered from candidate {idx + 1} ({prov_id}/{mod_id}): {exc.message}")

        # All candidate providers failed
        audit_engine.record_event(
            action="EXECUTION_ORCHESTRATED_FAILURE",
            resource="models/all",
            user_id=ctx.user_id,
            workspace_id=ctx.workspace_id,
            new_value=f"ReqID: {ctx.request_id} | All candidate providers failed",
        )

        raise SentinelExecutionOrchestrationError(
            message=f"All candidate LLM providers failed execution: {last_failover_exc}",
            details={"bypassed_providers": ctx.bypassed_providers, "correlation_id": ctx.correlation_id},
        )


execution_orchestrator = ExecutionOrchestrator()
