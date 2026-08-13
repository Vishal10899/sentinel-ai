"""Production-grade unit and integration tests for Phase 1.2 Enterprise Provider Management."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.providers import provider_manager
from app.providers.security import decrypt_secret, encrypt_secret, mask_api_key

from app.api.dependencies import current_user
from app.models.user import User
from app.rbac import rbac_engine

rbac_engine.check_permission = lambda *args, **kwargs: True
app.dependency_overrides[current_user] = lambda: User(
    id="admin", name="Admin", email="admin@sentinel.ai", salt="s", password_hash="h"
)

client = TestClient(app)


def test_api_key_masking_and_security():
    """Verify masking and encryption of API credentials."""
    assert mask_api_key(None) is None
    assert mask_api_key("") is None
    assert mask_api_key("sk-12345") == "****45"
    assert mask_api_key("sk-proj-1234567890abcdef") == "sk-pro****cdef"

    secret = "sk-test-secret-key-1234"
    enc = encrypt_secret(secret)
    assert enc.startswith("enc:")
    dec = decrypt_secret(enc)
    assert dec == secret


def test_provider_list_endpoint():
    """Verify GET /api/v1/providers returns provider configurations."""
    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/providers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        first = data[0]
        assert "provider_id" in first
        assert "provider_name" in first
        assert "status" in first
        assert "supports_streaming" in first


def test_provider_crud_operations():
    """Verify Create, Read, Update, Delete lifecycle for provider management."""
    with TestClient(app) as test_client:
        # Create custom provider
        create_res = test_client.post(
            "/api/v1/providers",
            json={
                "provider_id": "test_provider",
                "provider_name": "Test Enterprise Provider",
                "api_key": "sk-test-key-123456",
                "base_url": "https://api.testprovider.com",
                "default_model": "test-v1",
                "priority": 5,
                "cost_multiplier": 1.2,
                "supports_streaming": True,
                "supports_vision": True,
            },
        )
        assert create_res.status_code == 201
        created = create_res.json()
        assert created["provider_id"] == "test_provider"
        assert created["api_key_masked"] == "sk-tes****3456"
        assert created["cost_multiplier"] == 1.2

        # Read provider details
        detail_res = test_client.get("/api/v1/providers/test_provider")
        assert detail_res.status_code == 200
        assert detail_res.json()["provider_name"] == "Test Enterprise Provider"

        # Update provider configuration
        update_res = test_client.put(
            "/api/v1/providers/test_provider/configuration",
            json={
                "timeout_seconds": 45,
                "retry_count": 5,
                "priority": 2,
            },
        )
        assert update_res.status_code == 200
        updated = update_res.json()
        assert updated["timeout_seconds"] == 45
        assert updated["retry_count"] == 5

        # Delete provider
        del_res = test_client.delete("/api/v1/providers/test_provider")
        assert del_res.status_code == 204

        # Confirm 404 after deletion
        get_res = test_client.get("/api/v1/providers/test_provider")
        assert get_res.status_code == 404


def test_provider_connection_test_and_health_check():
    """Verify live connection testing and health check endpoints."""
    with TestClient(app) as test_client:
        # Connection test on OpenAI
        test_res = test_client.post("/api/v1/providers/openai/test")
        assert test_res.status_code == 200
        test_data = test_res.json()
        assert "valid" in test_data
        assert "latency_ms" in test_data
        assert "status" in test_data

        # Health check on OpenAI
        health_res = test_client.post("/api/v1/providers/openai/health-check")
        assert health_res.status_code == 200
        health_data = health_res.json()
        assert health_data["provider_id"] == "openai"


def test_provider_failover_and_toggle():
    """Verify failover rules and enable/disable toggle."""
    with TestClient(app) as test_client:
        # Toggle disable
        toggle_res = test_client.post("/api/v1/providers/openai/toggle?enabled=false")
        assert toggle_res.status_code == 200
        assert toggle_res.json()["enabled"] is False

        # Toggle enable back
        toggle_res2 = test_client.post("/api/v1/providers/openai/toggle?enabled=true")
        assert toggle_res2.status_code == 200
        assert toggle_res2.json()["enabled"] is True

        # Configure failover
        failover_res = test_client.put(
            "/api/v1/providers/openai/failover",
            json={
                "primary_provider_id": "openai",
                "secondary_provider_id": "gemini",
                "auto_failover": True,
            },
        )
        assert failover_res.status_code == 200
        failover_data = failover_res.json()
        assert failover_data["secondary_provider_id"] == "gemini"
        assert failover_data["auto_failover"] is True
