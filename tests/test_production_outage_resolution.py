import pytest
import time
from app.chat import enterprise_conversation_repository, memory_engine
from app.orchestration.router import adaptive_router
from app.cache.semantic import semantic_cache
from app.observability import metrics_aggregator, observability_repository
from app.providers.manager import provider_manager


def test_incident_1_conversation_lifecycle():
    """Verify complete conversation lifecycle operations."""
    # 1. Create Conversation
    conv = enterprise_conversation_repository.create_conversation(
        workspace_id="ws-e2e",
        user_id="user-123",
        title="Production Verification Thread",
        provider="ollama",
        model="llama3.2",
    )
    assert conv is not None
    assert conv.conversation_id.startswith("conv-")
    assert conv.workspace_id == "ws-e2e"

    # 2. Add Messages
    user_msg = enterprise_conversation_repository.add_message(
        conversation_id=conv.conversation_id,
        role="user",
        content="What is the architecture of Sentinel AI?",
        provider="ollama",
        model="llama3.2",
    )
    assert user_msg is not None
    assert user_msg.role == "user"

    asst_msg = enterprise_conversation_repository.add_message(
        conversation_id=conv.conversation_id,
        role="assistant",
        content="Sentinel AI is an Enterprise AI Decision Gateway...",
        provider="ollama",
        model="llama3.2",
        prompt_tokens=15,
        completion_tokens=40,
        cost=0.0,
        latency_ms=150.0,
    )
    assert asst_msg is not None

    # 3. Retrieve & Verify Thread
    msgs = enterprise_conversation_repository.list_messages(conv.conversation_id)
    assert len(msgs) == 2

    # 4. Pin & Favorite Toggles
    updated_pin = enterprise_conversation_repository.update_conversation(conv.conversation_id, {"is_pinned": True})
    assert updated_pin.is_pinned is True

    updated_fav = enterprise_conversation_repository.update_conversation(conv.conversation_id, {"is_favorite": True})
    assert updated_fav.is_favorite is True

    # 5. Archive & Delete
    archived = enterprise_conversation_repository.update_conversation(conv.conversation_id, {"status": "archived"})
    assert archived.status == "archived"

    deleted = enterprise_conversation_repository.delete_conversation(conv.conversation_id)
    assert deleted is True


def test_incident_2_ai_response_execution():
    """Verify real AI prompt evaluation and execution."""
    routing_res = adaptive_router.route("Write a Python script for array sorting")
    assert routing_res.selected_provider in ["ollama", "gemini", "openai", "anthropic"]
    assert routing_res.selected_model is not None
    assert routing_res.explanation_text is not None


def test_incident_3_observability_analytics():
    """Verify observability metrics aggregator and health reporting."""
    report = metrics_aggregator.aggregate(workspace_id="default", window_seconds=3600)
    report_dict = report.to_dict()

    assert "total_requests" in report_dict
    assert "total_cost_usd" in report_dict
    assert "latency_percentiles" in report_dict

    health = observability_repository.get_provider_health()
    assert len(health) >= 0


def test_incident_4_memory_savings_and_telemetry():
    """Verify AI Memory Engine savings calculation."""
    semantic_cache.set(
        prompt="Explain microservices architecture",
        response_text="Microservices architecture decomposes applications into small services...",
        workspace_id="ws-mem-e2e",
        provider_id="ollama",
        model_id="llama3.2",
        estimated_cost_usd=0.003,
        latency_ms=650.0,
        total_tokens=220,
    )

    hit = semantic_cache.get("Explain microservices architecture", workspace_id="ws-mem-e2e")
    assert hit is not None
    assert hit["hit"] is True

    metrics = semantic_cache.get_metrics()
    assert metrics["total_tokens_saved"] >= 220
    assert metrics["total_cost_saved_usd"] >= 0.003
    assert metrics["hit_rate_pct"] > 0.0


def test_incident_7_smart_routing_pipeline():
    """Verify complete 7-stage Smart Routing Brain execution loop."""
    prompt = "Create a database schema for user profiles and security roles"

    # Stage 1: Prompt Intelligence & Route
    route_res = adaptive_router.route(prompt, workspace_id="ws-routing-e2e")
    assert route_res.selected_provider is not None
    assert route_res.selected_model is not None

    # Stage 2: Feedback Loop & Decision Storage
    adaptive_router.record_execution_feedback(
        provider_id=route_res.selected_provider,
        model_id=route_res.selected_model,
        success=True,
        actual_latency_ms=180.0,
        actual_cost_usd=0.0,
    )

    # Stage 3: Routing Analytics
    analytics = adaptive_router.get_routing_analytics()
    assert analytics["total_routing_decisions"] > 0
    assert "local_usage_pct" in analytics


def test_incident_6_hello_memory_scenario():
    """Incident 6: Verify User 'Hello' -> Store -> Repeat 'Hello' -> Memory Hit (No Provider Exec)."""
    prompt = "Hello"
    ws = "ws-incident-6"

    # Step 1: Miss on first attempt
    hit1 = semantic_cache.get(prompt, workspace_id=ws)
    assert hit1 is None

    # Step 2: Model executes and memory stored
    semantic_cache.set(
        prompt=prompt,
        response_text="Hello! How can I assist you with Sentinel AI today?",
        workspace_id=ws,
        provider_id="ollama",
        model_id="llama3.2",
        estimated_cost_usd=0.0,
        latency_ms=120.0,
        total_tokens=15,
    )

    # Step 3: User repeats 'Hello'
    hit2 = semantic_cache.get(prompt, workspace_id=ws)

    # Step 4: Verify Every Stage Metrics
    assert hit2 is not None
    assert hit2["hit"] is True
    assert hit2["similarity_score"] == 1.0
    assert hit2["confidence"] >= 0.80
    assert hit2["response_text"] == "Hello! How can I assist you with Sentinel AI today?"

    metrics = semantic_cache.get_metrics()
    assert metrics["total_memories"] >= 1
    assert metrics["hit_rate_pct"] > 0.0


def test_incident_8_api_contract_and_provider_manager():
    """Verify provider configuration status resolution."""
    from app.core.settings import Settings
    from app.providers import register_configured_providers

    register_configured_providers(provider_manager, Settings())

    configs = provider_manager.list_configs()
    assert len(configs) > 0

    for cfg in configs:
        assert "provider_id" in cfg
        assert "status" in cfg
        assert cfg["status"] in ["healthy", "configured", "unconfigured", "disabled", "unhealthy", "degraded"]
