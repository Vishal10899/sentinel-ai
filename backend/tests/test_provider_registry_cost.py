"""Comprehensive Unit & Performance Test Suite for Sprint 2.4 + 2.5.

Tests Provider Registry, Capability Matrix, Pricing Engine, Cost Comparison,
Optimization Recommendations, Admin Operations, and Performance Benchmarks.
"""

from decimal import Decimal
import time
import pytest

from app.cost import (
    CostComparisonReport,
    CostOptimizationReport,
    DetailedCostEstimate,
    cost_comparator,
    cost_optimization_engine,
    pricing_engine,
)
from app.models_registry import model_registry
from app.models_registry.capability_matrix import capability_matrix_engine


# ====================================================
# 1. Provider Registry & Model Catalog Tests
# ====================================================

def test_registry_loading():
    providers = model_registry.list_providers()
    models = model_registry.list_models()

    assert len(providers) >= 4
    assert len(models) >= 10

    gemini = model_registry.get_provider("gemini")
    assert gemini.provider_name == "Google"

    flash = model_registry.get_model("gemini", "gemini-2.0-flash")
    assert flash.display_name == "Gemini 2.0 Flash"
    assert flash.context_window >= 1_000_000


def test_capability_matrix_generation():
    matrix = model_registry.get_capability_matrix()

    assert "gemini/gemini-2.0-flash" in matrix
    flash_profile = matrix["gemini/gemini-2.0-flash"]

    assert flash_profile.supports_chat is True
    assert flash_profile.supports_coding is True
    assert flash_profile.supports_vision is True
    assert flash_profile.supports_long_context is True


# ====================================================
# 2. Pricing & Cost Estimation Tests
# ====================================================

def test_pricing_calculation():
    est = pricing_engine.calculate_cost(
        provider_id="gemini",
        model_id="gemini-2.0-flash",
        prompt_tokens=1000,
        completion_tokens=1000,
        cached_tokens=500,
        reasoning_tokens=0,
    )

    assert isinstance(est, DetailedCostEstimate)
    assert float(est.prompt_cost_usd) > 0
    assert float(est.completion_cost_usd) > 0
    assert float(est.total_cost_usd) > 0


def test_cost_comparison_engine():
    report = cost_comparator.compare_all(
        prompt_tokens=2000,
        completion_tokens=1000,
        baseline_provider="openai",
        baseline_model="gpt-4o",
    )

    assert isinstance(report, CostComparisonReport)
    assert len(report.comparisons) >= 5
    assert report.cheapest_model is not None
    assert report.max_savings_pct >= 0.0


# ====================================================
# 3. Rule-Based Optimization Engine Tests
# ====================================================

def test_cost_optimization_engine():
    report = cost_optimization_engine.generate_recommendations(
        prompt="Short query",
        selected_provider="openai",
        selected_model="gpt-5",
        prompt_tokens=100,
    )

    assert isinstance(report, CostOptimizationReport)
    assert report.total_recommendations >= 1
    rule_ids = [r.rule_id for r in report.recommendations]
    assert "OPT-001" in rule_ids  # Overuse of premium model


# ====================================================
# 4. Service-Layer Admin Operations Tests
# ====================================================

def test_admin_operations():
    # Test disable & enable provider
    model_registry.disable_provider("anthropic")
    disabled = model_registry.get_provider("anthropic")
    assert disabled.enabled is False

    model_registry.enable_provider("anthropic")
    enabled = model_registry.get_provider("anthropic")
    assert enabled.enabled is True

    # Test deprecate model
    deprecated = model_registry.deprecate_model("openai", "gpt-4.1")
    assert deprecated.deprecated is True

    # Test change priority
    updated_priority = model_registry.change_priority("gemini", "gemini-2.0-flash", 1)
    assert updated_priority.priority == 1


# ====================================================
# 5. Performance Benchmarks Tests
# ====================================================

def test_performance_benchmarks():
    # 1. Registry Lookup (< 1ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        model_registry.get_model("gemini", "gemini-2.0-flash")
    lookup_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert lookup_ms < 1.0, f"Registry lookup took {lookup_ms:.3f} ms (limit 1.0 ms)"

    # 2. Cost Estimation (< 2ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        pricing_engine.calculate_cost("gemini", "gemini-2.0-flash", 1000, 500)
    cost_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert cost_ms < 2.0, f"Cost estimation took {cost_ms:.3f} ms (limit 2.0 ms)"

    # 3. Provider Comparison (< 5ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        cost_comparator.compare_all(1000, 500)
    compare_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert compare_ms < 5.0, f"Cost comparison took {compare_ms:.3f} ms (limit 5.0 ms)"
