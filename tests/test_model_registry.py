"""Tests for Phase 1.1 Enterprise Model Registry."""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models_registry import ModelRegistry, model_registry
from app.models_registry.schemas import ModelMetadata, ProviderMetadata

client = TestClient(app)


def test_model_metadata_extended_fields():
    """Verify ModelMetadata holds all required enterprise fields."""
    model = ModelMetadata(
        provider_id="openai",
        provider_name="OpenAI",
        model_id="gpt-4o",
        display_name="GPT-4o",
        category="chat",
        capabilities=frozenset({"chat", "vision", "function_calling"}),
        cost_per_1k_input_tokens=Decimal("0.0025"),
        cost_per_1k_output_tokens=Decimal("0.010"),
        average_latency_ms=450,
        priority=10,
        context_window=128000,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_audio=False,
        reasoning_score=88.0,
        speed_score=88.0,
        quality_score=93.0,
        enabled=True,
        deprecated=False,
    )
    assert model.provider_id == "openai"
    assert model.model_id == "gpt-4o"
    assert model.category == "chat"
    assert model.max_output_tokens == 4096
    assert model.supports_vision is True
    assert model.reasoning_score == 88.0


def test_model_metadata_validation():
    """Verify validation rules on ModelMetadata."""
    with pytest.raises(ValueError, match="cannot be empty"):
        ModelMetadata(
            provider_id="",
            provider_name="OpenAI",
            model_id="test",
            display_name="Test",
            capabilities=frozenset({"chat"}),
            cost_per_1k_input_tokens=Decimal("0"),
            cost_per_1k_output_tokens=Decimal("0"),
            average_latency_ms=100,
            priority=1,
            context_window=1000,
        )

    with pytest.raises(ValueError, match="cannot be negative"):
        ModelMetadata(
            provider_id="openai",
            provider_name="OpenAI",
            model_id="test",
            display_name="Test",
            capabilities=frozenset({"chat"}),
            cost_per_1k_input_tokens=Decimal("-1"),
            cost_per_1k_output_tokens=Decimal("0"),
            average_latency_ms=100,
            priority=1,
            context_window=1000,
        )


def test_registry_list_models_filtering():
    """Verify listing and filtering by provider and category."""
    models = model_registry.list_models(provider="openai")
    assert len(models) > 0
    assert all(m.provider_id == "openai" for m in models)

    reasoning_models = model_registry.list_models(category="reasoning")
    assert len(reasoning_models) > 0
    assert all(m.category == "reasoning" for m in reasoning_models)


def test_api_list_models_endpoint():
    """Verify GET /api/v1/models exposes extended metadata."""
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    first = data[0]
    assert "category" in first
    assert "max_output_tokens" in first
    assert "supports_streaming" in first
    assert "supports_function_calling" in first
    assert "supports_vision" in first
    assert "supports_audio" in first
    assert "reasoning_score" in first
    assert "speed_score" in first
    assert "quality_score" in first
    assert "deprecated" in first


def test_api_get_model_detail_endpoint():
    """Verify GET /api/v1/models/{provider_id}/{model_id} endpoint."""
    response = client.get("/api/v1/models/openai/gpt-4o")
    assert response.status_code == 200
    data = response.json()
    assert data["provider_id"] == "openai"
    assert data["model_id"] == "gpt-4o"
    assert data["display_name"] == "GPT-4o"
    assert data["supports_vision"] is True

    # Unknown model should 404
    err_response = client.get("/api/v1/models/openai/nonexistent-model")
    assert err_response.status_code == 404


def test_routing_and_cost_engine_compatibility():
    """Verify routing and cost endpoints work with updated registry."""
    with TestClient(app) as test_client:
        # Routing
        route_res = test_client.post(
            "/api/v1/routing/route",
            json={"task_category": "chat", "strategy": "balanced"},
        )
        assert route_res.status_code == 200
        route_data = route_res.json()
        assert "provider_id" in route_data
        assert "model_id" in route_data

        # Cost estimate
        cost_res = test_client.post(
            "/api/v1/cost/estimate",
            json={
                "provider_id": "openai",
                "model_id": "gpt-4o",
                "input_tokens": 1000,
                "output_tokens": 500,
            },
        )
        assert cost_res.status_code == 200
        cost_data = cost_res.json()
        assert float(cost_data["estimated_cost_usd"]) > 0
