"""Comprehensive Unit Tests for Phase 2 - Sprint 2.3: Enterprise Execution Orchestrator."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.orchestration.exceptions import (
    SentinelAuthenticationError,
    SentinelExecutionOrchestrationError,
    SentinelInvalidRequestError,
    SentinelProviderTimeoutError,
    SentinelProviderUnavailableError,
    SentinelRateLimitError,
)
from app.orchestration.execution_orchestrator import (
    ExecutionContext,
    ExecutionOrchestrator,
    NormalizedExecutionResponse,
    execution_orchestrator,
)
from app.providers.base import BaseProvider
from app.providers.manager import provider_manager
from app.routing.engine import FullRoutingDecision
from app.routing.scoring import CandidateScoreBreakdown


class MockProviderAdapter(BaseProvider):

    def __init__(self, name: str, fail_count: int = 0, fail_exc: Exception | None = None) -> None:
        self._name = name
        self._fail_count = fail_count
        self._fail_exc = fail_exc
        self.invocations = 0

    @property
    def name(self) -> str:
        return self._name

    async def generate(self, prompt: str, **options) -> str:
        self.invocations += 1
        if self.invocations <= self._fail_count and self._fail_exc:
            raise self._fail_exc
        return f"Response from {self._name} for prompt: {prompt}"

    async def stream_generate(self, prompt: str, **options):
        yield f"Chunk from {self._name}"

    async def embed(self, text: str, **options) -> list[float]:
        return [0.1, 0.2]

    async def health(self) -> dict:
        return {"status": "healthy"}

    async def test_connection(self) -> dict:
        return {"status": "ok"}


@pytest.fixture
def mock_routing_decision():
    cands = (
        CandidateScoreBreakdown(
            provider_id="mock_primary",
            model_id="primary-model",
            overall_score=95.0,
            rank=1,
            task_match_score=95.0,
            complexity_match_score=90.0,
            latency_score=90.0,
            cost_score=90.0,
            health_score=100.0,
            cost_per_1k_tokens=0.0003,
            latency_ms=15.0,
            status="active",
            reason="Rank 1 Winner",
        ),
        CandidateScoreBreakdown(
            provider_id="mock_secondary",
            model_id="secondary-model",
            overall_score=90.0,
            rank=2,
            task_match_score=90.0,
            complexity_match_score=90.0,
            latency_score=85.0,
            cost_score=85.0,
            health_score=100.0,
            cost_per_1k_tokens=0.001,
            latency_ms=25.0,
            status="active",
            reason="Rank 2 Candidate",
        ),
    )

    return FullRoutingDecision(
        selected_provider="mock_primary",
        selected_model="primary-model",
        strategy_used="balanced",
        primary_reason="Primary winner",
        intent_detected="general_chat",
        intent_confidence=0.9,
        complexity_level="simple",
        complexity_score=2.0,
        estimated_cost_usd=0.0003,
        estimated_latency_ms=15,
        estimated_savings_pct=80.0,
        ranked_candidates=cands,
        rejected_providers=(),
        alternative_models=("mock_secondary/secondary-model",),
    )


# ====================================================
# 1. Successful Execution Test
# ====================================================

@pytest.mark.anyio
async def test_successful_execution(mock_routing_decision):
    primary_adapter = MockProviderAdapter("mock_primary")
    with patch.object(provider_manager, "get", return_value=primary_adapter):
        ctx = ExecutionContext(correlation_id="corr-test-123")
        res = await execution_orchestrator.execute(
            prompt="Hello Sentinel AI",
            routing_decision=mock_routing_decision,
            context=ctx,
        )

        assert isinstance(res, NormalizedExecutionResponse)
        assert res.provider == "mock_primary"
        assert res.model == "primary-model"
        assert "Hello Sentinel AI" in res.content
        assert res.correlation_id == "corr-test-123"
        assert res.retry_count == 0
        assert res.failover_count == 0


# ====================================================
# 2. Transient Retry Policy Test
# ====================================================

@pytest.mark.anyio
async def test_transient_retry_success(mock_routing_decision):
    # Fails first invocation with 503, succeeds on retry #2
    transient_exc = SentinelProviderUnavailableError("503 Service Unavailable")
    primary_adapter = MockProviderAdapter("mock_primary", fail_count=1, fail_exc=transient_exc)

    with patch.object(provider_manager, "get", return_value=primary_adapter):
        ctx = ExecutionContext(max_retries=2)
        res = await execution_orchestrator.execute(
            prompt="Retry test prompt",
            routing_decision=mock_routing_decision,
            context=ctx,
        )

        assert res.provider == "mock_primary"
        assert res.retry_count == 1
        assert res.failover_count == 0


# ====================================================
# 3. Failover Execution Test
# ====================================================

@pytest.mark.anyio
async def test_failover_on_auth_failure(mock_routing_decision):
    # Primary fails with 401 Auth (non-transient). Should trigger instant failover to secondary.
    auth_exc = SentinelAuthenticationError("401 Unauthorized API Key")
    primary_adapter = MockProviderAdapter("mock_primary", fail_count=5, fail_exc=auth_exc)
    secondary_adapter = MockProviderAdapter("mock_secondary")

    def mock_get(provider_id):
        if provider_id == "mock_primary":
            return primary_adapter
        elif provider_id == "mock_secondary":
            return secondary_adapter
        return None

    with patch.object(provider_manager, "get", side_effect=mock_get):
        ctx = ExecutionContext()
        res = await execution_orchestrator.execute(
            prompt="Failover prompt",
            routing_decision=mock_routing_decision,
            context=ctx,
        )

        assert res.provider == "mock_secondary"
        assert res.model == "secondary-model"
        assert res.failover_count == 1
        assert len(res.bypassed_providers) == 1
        assert "mock_primary/primary-model" in res.bypassed_providers[0]


# ====================================================
# 4. Timeout Management Test
# ====================================================

@pytest.mark.anyio
async def test_timeout_triggers_failover(mock_routing_decision):
    # Mock primary adapter sleeping longer than timeout
    async def slow_generate(prompt, **kwargs):
        await asyncio.sleep(0.5)
        return "Slow response"

    primary_adapter = MockProviderAdapter("mock_primary")
    primary_adapter.generate = slow_generate

    secondary_adapter = MockProviderAdapter("mock_secondary")

    def mock_get(provider_id):
        return primary_adapter if provider_id == "mock_primary" else secondary_adapter

    with patch.object(provider_manager, "get", side_effect=mock_get):
        ctx = ExecutionContext(timeout_seconds=0.05, max_retries=1)
        res = await execution_orchestrator.execute(
            prompt="Timeout test",
            routing_decision=mock_routing_decision,
            context=ctx,
        )

        assert res.provider == "mock_secondary"
        assert res.failover_count == 1


# ====================================================
# 5. All Providers Failed Error Handling Test
# ====================================================

@pytest.mark.anyio
async def test_all_providers_failed(mock_routing_decision):
    failing_adapter = MockProviderAdapter("mock_failing", fail_count=10, fail_exc=SentinelAuthenticationError("401 Invalid Key"))

    with patch.object(provider_manager, "get", return_value=failing_adapter):
        ctx = ExecutionContext()
        with pytest.raises(SentinelExecutionOrchestrationError) as exc_info:
            await execution_orchestrator.execute(
                prompt="All fail prompt",
                routing_decision=mock_routing_decision,
                context=ctx,
            )

        assert "All candidate LLM providers failed execution" in str(exc_info.value)


# ====================================================
# 6. Request Validation Test
# ====================================================

@pytest.mark.anyio
async def test_empty_prompt_validation(mock_routing_decision):
    with pytest.raises(SentinelInvalidRequestError):
        await execution_orchestrator.execute(
            prompt="   ",
            routing_decision=mock_routing_decision,
        )
