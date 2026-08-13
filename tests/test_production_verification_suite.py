"""Verification suite for Part 1 & Part 4 requirements:

1. Test Provider API Key Update in RAM (live re-initialization without restarting Docker).
2. Test Strict Disabled Guard (returns HTTP 503 Provider Unavailable when all providers are disabled).
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.api.dependencies import current_user
from app.core.settings import settings
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.providers import provider_manager, register_configured_providers
from app.rbac import rbac_engine


async def override_get_db():
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with TestingSessionLocal() as session:
        yield session


def get_test_user():
    return User(
        id="admin_user_id",
        name="Admin User",
        email="admin@sentinel.ai",
        salt="salt",
        password_hash="hash",
    )


async def override_current_user():
    return get_test_user()


@pytest_asyncio.fixture
async def async_client():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[current_user] = override_current_user

    # Bypass RBAC check for test client
    rbac_engine.check_permission = lambda *args, **kwargs: True

    provider_manager.clear()
    register_configured_providers(provider_manager, settings)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_provider_api_key_update_live_reinitialization(async_client: AsyncClient):
    """Test 1: Update Gemini key via API, set model to gemini-2.0-flash, leave Base URL blank,

    and verify in RAM that active client re-initialized without restarting Docker.
    """
    new_key = "sk-gemini-live-test-key-9999"
    update_res = await async_client.put(
        "/api/v1/providers/gemini/configuration",
        json={
            "api_key": new_key,
            "model": "gemini-2.0-flash",
            "base_url": "",  # Blank base URL should sanitize to default endpoint
            "enabled": True,
        },
    )
    assert update_res.status_code == 200, f"Response text: {update_res.text}"
    body = update_res.json()
    assert body["provider_id"] == "gemini"
    assert body["enabled"] is True
    assert body["configured_model"] == "gemini-2.0-flash"
    assert body["base_url"] == "https://generativelanguage.googleapis.com"

    # Verify live adapter state in RAM without container restart
    gemini_adapter = provider_manager.get_provider("gemini")
    assert gemini_adapter._api_key == new_key
    assert gemini_adapter._model == "gemini-2.0-flash"
    assert gemini_adapter._base_url == "https://generativelanguage.googleapis.com"
    assert gemini_adapter._client is not None


@pytest.mark.asyncio
async def test_strict_disabled_provider_guard_returns_http_503(async_client: AsyncClient):
    """Test 2: Disable all providers (Ollama, Gemini, OpenAI, Anthropic), trigger routing/chat,

    and verify the backend returns an HTTP 503 error response instead of attempting Ollama execution.
    """
    # Explicitly disable all registered providers
    for p_name in provider_manager.provider_names():
        provider_manager.configure(p_name, enabled=False)

    # Verify provider_manager indicates no active providers
    for p_name in provider_manager.provider_names():
        assert provider_manager.is_active(p_name) is False

    # Trigger Chat endpoint when all enabled providers are disabled
    chat_res = await async_client.post(
        "/api/v1/chat",
        json={
            "prompt": "Test prompt with all providers disabled",
            "strategy": "adaptive",
        },
    )
    assert chat_res.status_code == 503
    assert chat_res.json()["detail"] == "No active enabled providers available for routing"

    # Re-enable gemini to restore provider state
    provider_manager.configure("gemini", enabled=True, api_key="sk-snt-demo-gemini-key")
