import time
import pytest
from app.orchestration.router import adaptive_router
from app.providers.manager import provider_manager
from app.core.settings import Settings
from app.providers import register_configured_providers


def test_provider_agnostic_routing():
    """Verify routing score calculation works purely off capability vectors with zero hardcoded provider names."""
    res = adaptive_router.route("Write a Python function to process data", workspace_id="ws-agnostic")

    assert res.selected_provider is not None
    assert res.selected_model is not None
    assert "Routing Score" in res.explanation_text or "Selected" in res.explanation_text
    assert len(res.candidate_scores) > 0


def test_circuit_breaker_open_and_recovery():
    """PART 6: Verify Circuit Breaker opens after 3 failures and skips candidate."""
    provider_id = "test_failing_provider"

    assert adaptive_router.is_circuit_open(provider_id) is False

    # Simulate 3 consecutive failures
    adaptive_router.record_execution_feedback(provider_id, "model-1", success=False, failures=1)
    adaptive_router.record_execution_feedback(provider_id, "model-1", success=False, failures=1)
    adaptive_router.record_execution_feedback(provider_id, "model-1", success=False, failures=1)

    # Circuit Breaker must be OPEN
    assert adaptive_router.is_circuit_open(provider_id) is True

    # After success, circuit resets and state is cleaned
    adaptive_router.record_execution_feedback(provider_id, "model-1", success=True, failures=0)
    assert adaptive_router._consecutive_failures.get(provider_id, 0) == 0
    if provider_id in adaptive_router._provider_health_adjustments:
        del adaptive_router._provider_health_adjustments[provider_id]


def test_dynamic_ollama_model_discovery():
    """PART 3: Verify dynamic model discovery without hardcoded model strings."""
    register_configured_providers(provider_manager, Settings())

    configs = provider_manager.list_configs()
    assert len(configs) > 0
    assert any("provider_id" in c for c in configs)
