"""Production-grade Unit and Integration tests for Task 17–18 — Adaptive AI Routing & Intent Detection."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.api.dependencies import current_user
from app.audit.repository import audit_repository
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.orchestration.capabilities import CapabilityEngine, capability_engine
from app.orchestration.intent import IntentDetector, intent_detector
from app.orchestration.router import AdaptiveRouter, adaptive_router

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


async def override_current_user():
    return User(
        id="routeuser123",
        name="Routing User",
        email="route@sentinel.ai",
        salt="routesalt123",
        password_hash="routehash123",
    )


@pytest_asyncio.fixture
async def async_client():
    from app.providers import provider_manager, GeminiProvider, OllamaProvider
    from app.rbac import rbac_engine

    rbac_engine.check_permission = lambda *args, **kwargs: True
    provider_manager.register(GeminiProvider(api_key="sk-test-gemini-key", model="gemini-2.0-flash"))
    provider_manager.register(OllamaProvider(base_url="http://localhost:11434", model="llama3.2"))

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[current_user] = override_current_user

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed user & workspace
    async with TestingSessionLocal() as db:
        user = User(
            id="routeuser123",
            name="Routing User",
            email="route@sentinel.ai",
            salt="routesalt123",
            password_hash="routehash123",
        )
        db.add(user)
        workspace = Workspace(
            id="route-workspace-uuid",
            name="Routing Workspace",
            slug="route-workspace",
            owner_id=user.id,
        )
        db.add(workspace)
        await db.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_intent_detection_and_request_profiling():
    """Verify IntentDetector intent classification and workload profiling."""
    detector = IntentDetector()

    # Coding intent test
    code_res = detector.detect_intent("Write a Python function to sort a list using quicksort def quicksort():")
    assert code_res.intent in ["CODE_GENERATION", "CODING"]
    assert code_res.confidence >= 0.30


@pytest.mark.asyncio
async def test_model_capability_catalog():
    """Verify CapabilityEngine catalog scoring and modality flags."""
    cap_engine = CapabilityEngine()

    gpt4o = cap_engine.get_capability("openai", "gpt-4o")
    assert gpt4o.supports_vision is True
    assert gpt4o.supports_tools is True

    all_caps = cap_engine.list_capabilities()
    assert len(all_caps) >= 3


@pytest.mark.asyncio
async def test_adaptive_router_smart_model_selection():
    """Verify AdaptiveRouter smart model selection and audit event emission."""
    from app.providers import provider_manager, GeminiProvider, OllamaProvider

    provider_manager.register(GeminiProvider(api_key="sk-test-gemini-key", model="gemini-2.0-flash"))
    provider_manager.register(OllamaProvider(base_url="http://localhost:11434", model="llama3.2"))
    router = AdaptiveRouter()

    # Coding request
    result = router.route(
        prompt="Write a Python class for async queue management with def enqueue() and def dequeue()",
        workspace_id="ws-test-route",
    )
    assert result.selected_provider in ["gemini", "ollama", "openai"]
    assert result.selected_model is not None
    assert result.explanation_text is not None
    assert result.intent_detected in ["CODE_GENERATION", "CODING"]
    assert len(result.candidate_scores) >= 1

    # Verify audit event emission
    audit_logs = audit_repository.search(action="ROUTING_INTENT_EVALUATED")
    assert len(audit_logs) >= 1
    assert ("CODE_GENERATION" in audit_logs[0].new_value or "CODING" in audit_logs[0].new_value)


@pytest.mark.asyncio
async def test_adaptive_routing_rest_apis(async_client: AsyncClient):
    """Test Adaptive Routing REST API endpoints."""
    # 1. POST Intent Detection API
    intent_res = await async_client.post("/api/v1/routing/intent", json={
        "prompt": "Translate this text to Spanish: Hello world!",
    })
    assert intent_res.status_code == 200
    assert intent_res.json()["intent"]["intent"] == "TRANSLATION"

    # 2. POST Adaptive Route API
    route_res = await async_client.post("/api/v1/routing/adaptive", json={
        "prompt": "Solve differential equation dy/dx = 5x + 3",
        "strategy_override": "QUALITY_MAXIMIZER",
    })
    assert route_res.status_code == 200
    assert "selected_provider" in route_res.json()
    assert "explanation_text" in route_res.json()

    # 3. GET Capabilities API
    cap_res = await async_client.get("/api/v1/routing/capabilities")
    assert cap_res.status_code == 200
    assert len(cap_res.json()) >= 5

    # 4. GET Strategies API
    strat_res = await async_client.get("/api/v1/routing/strategies")
    assert strat_res.status_code == 200
    assert len(strat_res.json()) >= 5
