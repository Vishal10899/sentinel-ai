"""Comprehensive Unit, Integration, & Performance Test Suite for Sprint 2.6–2.7.

Tests Trace Engine Spans, Telemetry Aggregation, Runtime Policy Platform Rules,
Budget Enforcement, Prompt Security, Performance Benchmarks, and System Integrity.
"""

from decimal import Decimal
import time
import pytest

from app.cost import cost_comparator, pricing_engine
from app.models_registry import model_registry
from app.observability import metrics_aggregator, observability_repository, trace_engine
from app.orchestration.execution_orchestrator import ExecutionContext, execution_orchestrator
from app.policy import policy_engine, policy_repository
from app.policy.models import PolicyAction
from app.routing.engine import adaptive_routing_engine
from app.routing.explainability import explainability_engine
from app.routing.types import ModelInfo


# ====================================================
# 1. Trace Engine & Spans Unit Tests
# ====================================================

def test_trace_engine_and_spans():
    ctx = trace_engine.create_trace(
        conversation_id="conv-123",
        workspace_id="ws-enterprise",
        user_id="user-456",
        provider_id="gemini",
        model_id="gemini-2.0-flash",
        prompt="Explain quantum computing",
    )

    span_id, s_t = ctx.start_span("routing_decision_span")
    ctx.record_span("routing_decision_span", s_t, status="SUCCESS")

    trace_rec = ctx.finish(status="SUCCESS", response="Quantum computing explanation", tokens=120, cost_usd=0.0004)

    assert trace_rec.trace_id == ctx.trace_id
    assert len(trace_rec.spans) == 1
    assert trace_rec.spans[0].span_name == "routing_decision_span"
    assert trace_rec.cost_usd == 0.0004


# ====================================================
# 2. Metrics Aggregator Tests (< 5ms)
# ====================================================

def test_metrics_aggregator():
    # Record test trace
    ctx = trace_engine.create_trace(provider_id="gemini", model_id="gemini-2.0-flash", prompt="Test metrics")
    ctx.finish(status="SUCCESS", response="OK", tokens=50, cost_usd=0.0002)

    report = metrics_aggregator.aggregate(window_seconds=3600)

    assert report.total_requests >= 1
    assert report.requests_per_minute >= 0.0
    assert report.latency_percentiles.p50_ms >= 0.0
    assert "gemini" in report.cost_by_provider


# ====================================================
# 3. Policy Platform Rules & Budget Tests (< 2ms)
# ====================================================

def test_policy_allow_and_deny():
    # Allow test
    allow_decision = policy_engine.evaluate({"prompt": "Normal prompt", "workspace_id": "default"})
    assert allow_decision.action in (PolicyAction.ALLOW, PolicyAction.WARN)

    # Deny test with blocked provider
    test_policy = policy_repository.create_policy({
        "name": "Block OpenAI Policy",
        "workspace_id": "ws-restricted",
        "blocked_providers": ["openai"],
        "is_active": True,
    })

    deny_decision = policy_engine.evaluate({
        "prompt": "Hello",
        "workspace_id": "ws-restricted",
        "provider_id": "openai",
    })

    assert deny_decision.action == PolicyAction.DENY
    assert "explicitly blocked" in deny_decision.reason


def test_policy_prompt_security_pii_and_secrets():
    sec_policy = policy_repository.create_policy({
        "name": "Security Hardened Policy",
        "workspace_id": "ws-security",
        "detect_pii": True,
        "detect_secrets": True,
        "is_active": True,
    })

    # PII Email Detection
    pii_decision = policy_engine.evaluate({
        "prompt": "Please email me at user@enterprise.com with details",
        "workspace_id": "ws-security",
    })
    assert pii_decision.action == PolicyAction.DENY
    assert "PII" in pii_decision.reason

    # Secret API Key Detection
    secret_decision = policy_engine.evaluate({
        "prompt": "My API key is sk-proj-123456789012345678901234567890",
        "workspace_id": "ws-security",
    })
    assert secret_decision.action == PolicyAction.DENY
    assert "secret" in secret_decision.reason.lower()


def test_policy_fallback_on_premium_restriction():
    prem_policy = policy_repository.create_policy({
        "name": "Restrict Premium Models Policy",
        "workspace_id": "ws-budget",
        "restrict_premium_models": True,
        "fallback_model": "gemini-2.0-flash",
        "is_active": True,
    })

    fallback_decision = policy_engine.evaluate({
        "prompt": "Short code question",
        "workspace_id": "ws-budget",
        "model_id": "gpt-5",
    })

    assert fallback_decision.action == PolicyAction.FALLBACK
    assert fallback_decision.fallback_model == "gemini-2.0-flash"


# ====================================================
# 4. Performance Benchmarks Tests
# ====================================================

def test_performance_benchmarks():
    # 1. Observability Overhead (< 3ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        ctx = trace_engine.create_trace(prompt="Trace bench")
        ctx.finish(status="SUCCESS", response="OK")
    obs_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert obs_ms < 3.0, f"Observability overhead took {obs_ms:.3f} ms (limit 3.0 ms)"

    # 2. Policy Evaluation (< 2ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        policy_engine.evaluate({"prompt": "Policy bench", "workspace_id": "default"})
    pol_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert pol_ms < 2.0, f"Policy evaluation took {pol_ms:.3f} ms (limit 2.0 ms)"

    # 3. Metrics Aggregation (< 5ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        metrics_aggregator.aggregate(window_seconds=3600)
    agg_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert agg_ms < 5.0, f"Metrics aggregation took {agg_ms:.3f} ms (limit 5.0 ms)"


# ====================================================
# 5. Full Pipeline System Integrity Verification
# ====================================================

def test_full_pipeline_system_integrity():
    mock_candidates = [
        ModelInfo(
            provider="gemini",
            model_name="gemini-2.0-flash",
            category="chat",
            capabilities=frozenset({"code_generation", "chat"}),
            cost_per_1k_tokens=0.0001,
            latency=250,
            quality_score=90.0,
            speed_score=98.0,
            reasoning_score=85.0,
            priority=10,
            provider_status="healthy",
            supports_vision=True,
        ),
    ]

    # 1. Adaptive Router
    decision = adaptive_routing_engine.route("Write a Python script", strategy="balanced", candidates=mock_candidates)
    assert decision.selected_provider == "gemini"

    # 2. Explainability Engine
    explanation = explainability_engine.build_explanation(decision)
    assert explanation.explanation_generation_ms < 2.0

    # 3. Model Registry
    gemini = model_registry.get_model("gemini", "gemini-2.0-flash")
    assert gemini.display_name == "Gemini 2.0 Flash"

    # 4. Pricing Engine
    cost_est = pricing_engine.calculate_cost("gemini", "gemini-2.0-flash", 1000, 500)
    assert float(cost_est.total_cost_usd) > 0
