"""Comprehensive Unit & Performance Tests for Phase 2 - Sprint 2.2: Explainable AI Routing Engine."""

import json
import time
import pytest

from app.routing.engine import adaptive_routing_engine
from app.routing.explainability import RoutingExplanationEngine, explainability_engine
from app.routing.types import ModelInfo, TaskCategory


@pytest.fixture
def mock_candidate_models():
    return [
        ModelInfo(
            provider="gemini",
            model_name="gemini-2.0-flash",
            cost_per_1k_tokens=0.0003,
            latency=14.0,
            capabilities=frozenset([TaskCategory.CHAT, TaskCategory.CODE_GENERATION]),
            priority=1,
            category="chat",
            quality_score=92.0,
            reasoning_score=90.0,
            speed_score=98.0,
            provider_status="healthy",
        ),
        ModelInfo(
            provider="openai",
            model_name="gpt-4o",
            cost_per_1k_tokens=0.0025,
            latency=32.0,
            capabilities=frozenset([TaskCategory.CHAT, TaskCategory.CODE_GENERATION]),
            priority=2,
            category="chat",
            quality_score=96.0,
            reasoning_score=95.0,
            speed_score=85.0,
            provider_status="healthy",
        ),
        ModelInfo(
            provider="anthropic",
            model_name="claude-3-5-sonnet",
            cost_per_1k_tokens=0.0030,
            latency=28.0,
            capabilities=frozenset([TaskCategory.CHAT]),
            priority=3,
            category="chat",
            quality_score=98.0,
            reasoning_score=97.0,
            speed_score=88.0,
            provider_status="unhealthy",
        ),
    ]


# ====================================================
# 1. Explanation Generation Tests
# ====================================================

def test_explanation_generation_summary(mock_candidate_models):
    decision = adaptive_routing_engine.route(
        prompt="Explain the saga pattern in microservices",
        strategy="balanced",
        candidates=mock_candidate_models,
    )

    explanation = explainability_engine.build_explanation(decision)

    assert explanation.selected_provider in ("gemini", "openai", "anthropic")
    assert "Selected" in explanation.primary_reason_summary
    assert "Strategy: 'balanced'" in explanation.primary_reason_summary
    assert explanation.intent_detected is not None
    assert explanation.complexity_level is not None


# ====================================================
# 2. Candidate Ranking Explanation Tests
# ====================================================

def test_candidate_ranking_explanation(mock_candidate_models):
    decision = adaptive_routing_engine.route(
        prompt="Write a Python script",
        strategy="balanced",
        candidates=mock_candidate_models,
    )

    explanation = explainability_engine.build_explanation(decision)

    assert len(explanation.candidate_explanations) > 0
    winner = explanation.candidate_explanations[0]
    assert winner.rank == 1
    assert "Rank 1 Winner" in winner.tradeoff_summary
    assert "task_match" in winner.score_breakdown


# ====================================================
# 3. Rejected Model Explanation Tests
# ====================================================

def test_rejected_model_explanation(mock_candidate_models):
    decision = adaptive_routing_engine.route(
        prompt="Review code",
        strategy="balanced",
        candidates=mock_candidate_models,
    )

    explanation = explainability_engine.build_explanation(decision)

    assert len(explanation.rejected_explanations) >= 1
    rejected = explanation.rejected_explanations[0]
    assert rejected.provider_id == "anthropic"
    assert rejected.circuit_breaker_triggered is True


# ====================================================
# 4. Timeline Stage Generation Tests
# ====================================================

def test_timeline_stage_generation(mock_candidate_models):
    decision = adaptive_routing_engine.route(
        prompt="Calculate 2 + 2",
        strategy="balanced",
        candidates=mock_candidate_models,
    )

    explanation = explainability_engine.build_explanation(decision)

    assert len(explanation.timeline_stages) == 8
    stage_names = [t.stage_name for t in explanation.timeline_stages]
    assert "Prompt Received" in stage_names
    assert "Intent Detection" in stage_names
    assert "Complexity Analysis" in stage_names
    assert "Capability Matching" in stage_names
    assert "Health Filtering" in stage_names
    assert "Cost Estimation" in stage_names
    assert "Ranking" in stage_names
    assert "Final Selection" in stage_names


# ====================================================
# 5. JSON Serialization Tests
# ====================================================

def test_explanation_json_serialization(mock_candidate_models):
    decision = adaptive_routing_engine.route(
        prompt="Test JSON output",
        strategy="balanced",
        candidates=mock_candidate_models,
    )

    explanation = explainability_engine.build_explanation(decision)
    exp_dict = explanation.to_dict()

    json_str = json.dumps(exp_dict)
    assert isinstance(json_str, str)
    assert "primary_reason_summary" in json_str
    assert "timeline_stages" in json_str


# ====================================================
# 6. Performance Benchmark Test (< 2.0 ms constraint)
# ====================================================

def test_explanation_performance_benchmark(mock_candidate_models):
    decision = adaptive_routing_engine.route(
        prompt="Performance benchmark test query",
        strategy="balanced",
        candidates=mock_candidate_models,
    )

    # Warmup
    explainability_engine.build_explanation(decision)

    # Benchmark 100 executions
    start = time.perf_counter_ns()
    for _ in range(100):
        explainability_engine.build_explanation(decision)
    elapsed_ms = ((time.perf_counter_ns() - start) / 1_000_000) / 100.0

    # Ensure explanation building adds less than 2.0 ms processing time
    assert elapsed_ms < 2.0, f"Explanation generation took {elapsed_ms:.3f} ms, exceeding 2.0 ms limit"
