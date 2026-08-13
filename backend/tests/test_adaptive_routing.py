"""Comprehensive Unit Tests for Phase 2 - Sprint 2.1: Adaptive AI Routing Engine."""

from decimal import Decimal
import pytest

from app.routing.analyzer import PromptAnalyzer, prompt_analyzer
from app.routing.classifier import TaskCategoryV2, TaskClassifier, task_classifier
from app.routing.complexity import ComplexityAnalyzer, ComplexityLevel, complexity_analyzer
from app.routing.engine import AdaptiveAIRoutingEngine, adaptive_routing_engine
from app.routing.scoring import MultiFactorScoringEngine, scoring_engine
from app.routing.types import ModelInfo, TaskCategory


@pytest.fixture
def mock_candidate_models():
    return [
        ModelInfo(
            provider="gemini",
            model_name="gemini-2.0-flash",
            cost_per_1k_tokens=0.0003,
            latency=14.0,
            capabilities=frozenset([TaskCategory.CHAT, TaskCategory.CODE_GENERATION, TaskCategory.REASONING]),
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
            capabilities=frozenset([TaskCategory.CHAT, TaskCategory.CODE_GENERATION, TaskCategory.REASONING, TaskCategory.VISION]),
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
            capabilities=frozenset([TaskCategory.CHAT, TaskCategory.CODE_GENERATION, TaskCategory.REASONING]),
            priority=3,
            category="chat",
            quality_score=98.0,
            reasoning_score=97.0,
            speed_score=88.0,
            provider_status="healthy",
        ),
        ModelInfo(
            provider="ollama",
            model_name="llama3.2",
            cost_per_1k_tokens=0.0000,
            latency=6.0,
            capabilities=frozenset([TaskCategory.CHAT, TaskCategory.CODE_GENERATION]),
            priority=4,
            category="chat",
            quality_score=82.0,
            reasoning_score=78.0,
            speed_score=99.0,
            provider_status="healthy",
        ),
    ]


# ====================================================
# 1. Prompt Analysis Unit Tests
# ====================================================

def test_prompt_analysis_python_code():
    prompt = "def calculate_factorial(n: int) -> int:\n    return 1 if n <= 1 else n * calculate_factorial(n - 1)"
    res = prompt_analyzer.analyze(prompt)

    assert res.detected_language == "python"
    assert res.has_code is True
    assert res.output_format == "code"
    assert res.estimated_tokens > 0


def test_prompt_analysis_sql_query():
    prompt = "SELECT user_id, COUNT(*) FROM orders WHERE status = 'COMPLETED' GROUP BY user_id;"
    res = prompt_analyzer.analyze(prompt)

    assert res.detected_language == "sql"
    assert res.has_code is True
    assert res.output_format == "code"


def test_prompt_analysis_math_reasoning():
    prompt = "Solve the integral \\( \\int_0^1 x^2 dx \\) and explain step-by-step."
    res = prompt_analyzer.analyze(prompt)

    assert res.has_math is True
    assert res.reasoning_depth in ("medium", "high")


# ====================================================
# 2. Task Classification Unit Tests
# ====================================================

def test_task_classification_coding():
    res = task_classifier.classify("Write a Rust function to parse JSON headers", detected_language="rust")

    assert res.primary_category == TaskCategoryV2.CODING
    assert res.confidence >= 0.70


def test_task_classification_security_review():
    res = task_classifier.classify("Audit this JWT authentication handler for OWASP security vulnerabilities and secret leaks")

    assert res.primary_category == TaskCategoryV2.SECURITY_REVIEW
    assert res.confidence >= 0.70


def test_task_classification_summarization():
    res = task_classifier.classify("Summarize the attached Q3 financial report into bullet points key takeaways")

    assert res.primary_category == TaskCategoryV2.SUMMARIZATION
    assert res.confidence >= 0.70


# ====================================================
# 3. Complexity Analysis Unit Tests
# ====================================================

def test_complexity_analysis_simple():
    res = complexity_analyzer.analyze("What is the capital of France?", estimated_tokens=10)

    assert res.level == ComplexityLevel.SIMPLE
    assert res.score_1_to_10 < 3.0


def test_complexity_analysis_very_complex():
    long_code_prompt = "def complex_algo():\n" + ("    pass\n" * 60)
    res = complexity_analyzer.analyze(
        long_code_prompt,
        estimated_tokens=5000,
        reasoning_depth="high",
        has_code=True,
        has_files=True,
    )

    assert res.level == ComplexityLevel.VERY_COMPLEX
    assert res.score_1_to_10 >= 7.5


# ====================================================
# 4. Multi-Factor Scoring Unit Tests
# ====================================================

def test_scoring_engine_candidate_ranking(mock_candidate_models):
    scores = scoring_engine.evaluate(
        mock_candidate_models,
        task_category=TaskCategoryV2.CODING,
        complexity=ComplexityLevel.MEDIUM,
        strategy_name="balanced",
    )

    assert len(scores) == 4
    assert scores[0].rank == 1
    assert scores[0].overall_score >= scores[1].overall_score
    assert all(s.overall_score >= 0.0 for s in scores)


def test_scoring_engine_cheapest_strategy(mock_candidate_models):
    scores = scoring_engine.evaluate(
        mock_candidate_models,
        task_category=TaskCategoryV2.GENERAL_CHAT,
        complexity=ComplexityLevel.SIMPLE,
        strategy_name="cheapest",
    )

    # Local free model (ollama) or cheap model (gemini) should rank #1
    assert scores[0].provider_id in ("ollama", "gemini")


# ====================================================
# 5. Adaptive AI Routing Engine End-to-End Tests
# ====================================================

def test_adaptive_routing_engine_end_to_end(mock_candidate_models):
    decision = adaptive_routing_engine.route(
        prompt="Write a Python script to perform async database connection pooling",
        strategy="balanced",
        candidates=mock_candidate_models,
    )

    assert decision.selected_provider in ("gemini", "openai", "anthropic", "ollama")
    assert decision.intent_detected in ("coding", "code_review", "general_chat")
    assert decision.complexity_level in ("simple", "medium", "complex")
    assert decision.estimated_latency_ms > 0
    assert len(decision.ranked_candidates) == len(mock_candidate_models)
    assert decision.estimated_savings_pct >= 0.0


def test_adaptive_routing_engine_health_filtering(mock_candidate_models):
    # Set openai to unhealthy
    unhealthy_pool = [
        ModelInfo(
            provider="openai",
            model_name="gpt-4o",
            cost_per_1k_tokens=0.0025,
            latency=32.0,
            capabilities=frozenset([TaskCategory.CHAT]),
            priority=1,
            quality_score=99.0,
            provider_status="unhealthy",
        ),
        ModelInfo(
            provider="gemini",
            model_name="gemini-2.0-flash",
            cost_per_1k_tokens=0.0003,
            latency=14.0,
            capabilities=frozenset([TaskCategory.CHAT]),
            priority=2,
            quality_score=92.0,
            provider_status="healthy",
        ),
    ]

    decision = adaptive_routing_engine.route(
        prompt="Hello world",
        strategy="balanced",
        candidates=unhealthy_pool,
    )

    # Unhealthy OpenAI should be filtered out, selecting Gemini
    assert decision.selected_provider == "gemini"
    assert len(decision.rejected_providers) == 1
    assert "openai/gpt-4o" in decision.rejected_providers[0]


def test_adaptive_routing_engine_edge_case_empty_prompt(mock_candidate_models):
    decision = adaptive_routing_engine.route(
        prompt="",
        strategy="balanced",
        candidates=mock_candidate_models,
    )

    assert decision.selected_provider is not None
    assert decision.intent_detected == "general_chat"
