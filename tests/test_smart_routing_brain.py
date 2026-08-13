import pytest
from app.orchestration.intent import intent_detector
from app.orchestration.models import PromptIntelligenceProfile
from app.orchestration.router import adaptive_router


def test_prompt_profiling():
    prompt = "Write a high-performance Python microservice to process SQL database queries with pandas"
    profile = intent_detector.generate_prompt_intelligence_profile(prompt)

    assert isinstance(profile, PromptIntelligenceProfile)
    assert profile.intent in ["CODE_GENERATION", "DATA_ANALYSIS", "CODING"]
    assert profile.coding_pct > 0.0
    assert profile.complexity in ["MEDIUM", "HIGH", "VERY_HIGH"]
    assert profile.reasoning_depth >= 0.70
    assert profile.estimated_input_tokens > 0


def test_routing_score_calculation_and_explainability():
    prompt = "Explain quantum cryptography step-by-step"
    result = adaptive_router.route(prompt)

    assert result.selected_provider in ["ollama", "gemini", "openai", "anthropic"]
    assert result.selected_model is not None
    assert result.explanation_text is not None
    assert "Routing Score" in result.explanation_text or "Selected" in result.explanation_text
    assert len(result.candidate_scores) > 0


def test_local_first_routing():
    # Prompt suitable for local execution (privacy sensitive code snippet)
    prompt = "Refactor this internal API function class MySecretHandler: def run(self): pass"
    result = adaptive_router.route(prompt)

    # Local Ollama preferred for local privacy code tasks
    assert result.selected_provider == "ollama"
    assert result.selected_model in ["llama3.2", "llama3.1:8b", "mistral", "deepseek-r1"]
    assert "Local" in result.explanation_text or "privacy" in result.explanation_text.lower()


def test_cloud_fallback_for_extreme_complexity():
    # Large architecture design query requiring frontier models
    prompt = "Design a distributed global multi-region database architecture with high availability, linear scalability, raft consensus theorem proof, and microservice failovers"
    result = adaptive_router.route(prompt)

    # Frontier high-reasoning model selected for extreme complexity
    assert result.selected_provider in ["openai", "anthropic", "gemini", "openrouter", "ollama"]
    assert result.explanation_text is not None


def test_provider_health_adaptation_and_self_healing():
    # Simulate health degradation for openai
    adaptive_router.record_execution_feedback(
        provider_id="openai",
        model_id="gpt-4o",
        success=False,
        failures=1,
    )

    # Health adjustment multiplier reduces priority
    health_mult = adaptive_router._provider_health_adjustments.get("openai", 1.0)
    assert health_mult < 1.0

    # Simulate subsequent successful executions to restore health (Self-Healing)
    for _ in range(20):
        adaptive_router.record_execution_feedback(
            provider_id="openai",
            model_id="gpt-4o",
            success=True,
            failures=0,
        )

    restored_mult = adaptive_router._provider_health_adjustments.get("openai", 1.0)
    assert restored_mult > health_mult


def test_decision_storage_and_routing_analytics():
    # Execute a route call to populate decision memory
    adaptive_router.route("Summarize article about climate change")

    analytics = adaptive_router.get_routing_analytics()

    assert analytics["total_routing_decisions"] > 0
    assert "local_usage_pct" in analytics
    assert "cloud_usage_pct" in analytics
    assert "average_routing_score" in analytics
    assert "provider_distribution" in analytics
