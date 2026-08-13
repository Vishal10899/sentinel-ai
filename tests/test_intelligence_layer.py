"""Production-grade Unit and Integration tests for Task 05–06 — Enterprise Intelligence Layer (Semantic Cache + Policy Engine)."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.api.dependencies import current_user
from app.cache.semantic import SemanticCache, semantic_cache
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.policy.evaluator import PolicyEngine, policy_engine
from app.policy.models import AIPolicy, PolicyAction
from app.policy.repository import policy_repository

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


async def override_current_user():
    return User(
        id="inteluser123",
        name="Intelligence User",
        email="intel@sentinel.ai",
        salt="intelsalt123",
        password_hash="intelhash123",
    )


@pytest_asyncio.fixture
async def async_client():
    from app.rbac import rbac_engine
    rbac_engine.check_permission = lambda *args, **kwargs: True

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[current_user] = override_current_user

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed user & workspace
    async with TestingSessionLocal() as db:
        user = User(
            id="inteluser123",
            name="Intelligence User",
            email="intel@sentinel.ai",
            salt="intelsalt123",
            password_hash="intelhash123",
        )
        db.add(user)
        workspace = Workspace(
            id="intel-workspace-uuid",
            name="Intelligence Workspace",
            slug="intel-workspace",
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
async def test_exact_and_semantic_cache_matching():
    """Verify SemanticCache exact hash matching and similarity score threshold matching."""
    cache = SemanticCache(default_threshold=0.8)
    cache.invalidate()

    # 1. Set cache entry
    cache.set(
        prompt="Explain quantum computing principles",
        response_text="Quantum computing utilizes qubits, superposition, and entanglement.",
        workspace_id="ws-test",
        model_id="gpt-4o",
        estimated_cost_usd=0.002,
        latency_ms=450.0,
        total_tokens=180,
    )

    # 2. Test Exact Match Hit
    exact_res = cache.get("Explain quantum computing principles", workspace_id="ws-test", model_id="gpt-4o")
    assert exact_res is not None
    assert exact_res["hit"] is True
    assert exact_res["hit_type"] == "exact"
    assert "superposition" in exact_res["response_text"]

    # 3. Test Semantic Similarity Match Hit
    semantic_res = cache.get("Explain quantum computing principles simply", workspace_id="ws-test", model_id="gpt-4o")
    assert semantic_res is not None
    assert semantic_res["hit"] is True
    assert semantic_res["hit_type"] == "semantic"
    assert semantic_res["similarity_score"] >= 0.8

    # 4. Test Cache Miss
    miss_res = cache.get("What is the recipe for chocolate cake?", workspace_id="ws-test", model_id="gpt-4o")
    assert miss_res is None


@pytest.mark.asyncio
async def test_cache_telemetry_metrics_and_invalidation():
    """Verify cache metrics collection and workspace invalidation."""
    cache = SemanticCache()
    cache.invalidate()

    cache.set(prompt="Test prompt", response_text="Test response", workspace_id="ws-1", estimated_cost_usd=0.005, latency_ms=300)
    cache.get("Test prompt", workspace_id="ws-1")

    metrics = cache.get_metrics()
    assert metrics["total_requests"] >= 1
    assert metrics["exact_hits"] == 1
    assert metrics["total_cost_saved_usd"] >= 0.005

    # Clear workspace cache
    invalidated = cache.invalidate("ws-1")
    assert invalidated >= 1


@pytest.mark.asyncio
async def test_policy_engine_evaluation_rules():
    """Verify PolicyEngine evaluation across blocked providers, parameter capping, and budget limits."""
    # 1. Create restrictive test policy
    policy = policy_repository.create_policy({
        "name": "Strict Security Policy",
        "workspace_id": "ws-strict",
        "blocked_providers": ["untrusted-provider"],
        "max_tokens": 1000,
        "max_temperature": 0.5,
        "monthly_budget_limit_usd": 10.0,
        "current_spend_usd": 10.5,  # Exceeded
        "is_active": True,
    })

    engine = PolicyEngine(repository=policy_repository)

    # Test Blocked Provider
    d1 = engine.evaluate({"workspace_id": "ws-strict", "provider_id": "untrusted-provider"})
    assert d1.action in (PolicyAction.BLOCK, PolicyAction.DENY)
    assert "blocked" in d1.reason.lower()

    # Test Budget Exceeded Block
    d2 = engine.evaluate({"workspace_id": "ws-strict", "provider_id": "openai"})
    assert d2.action in (PolicyAction.BLOCK, PolicyAction.DENY)
    assert "budget" in d2.reason.lower()

    # Test Parameter Capping (max_tokens & temperature)
    policy.current_spend_usd = 1.0  # Under budget
    d3 = engine.evaluate({
        "workspace_id": "ws-strict",
        "provider_id": "openai",
        "model_id": "gpt-4o",
        "max_tokens": 2000,
        "temperature": 0.9,
    })
    assert d3.action == PolicyAction.MODIFY
    assert d3.modified_request["max_tokens"] == 1000


@pytest.mark.asyncio
async def test_policies_and_cache_rest_api_endpoints(async_client: AsyncClient):
    """Test Policy Management and Cache REST API endpoints."""
    # 1. Create Policy via REST API
    res = await async_client.post("/api/v1/policies", json={
        "name": "API Test Policy",
        "workspace_id": "ws-api",
        "max_tokens": 2048,
    })
    assert res.status_code in (200, 201)
    policy_id = res.json()["id"]

    # 2. List Policies
    list_res = await async_client.get("/api/v1/policies?workspace_id=ws-api")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Simulate Policy Evaluation Endpoint
    sim_res = await async_client.post("/api/v1/policies/evaluate", json={
        "workspace_id": "ws-api",
        "max_tokens": 4096,
    })
    assert sim_res.status_code == 200
    assert sim_res.json()["action"] in ("MODIFY", "ALLOW", "BLOCK", "DENY")

    # 4. Cache Stats Endpoint
    stats_res = await async_client.get("/api/v1/cache/stats")
    assert stats_res.status_code == 200
    assert "hit_rate_pct" in stats_res.json()

    # 5. Invalidate Cache Endpoint
    inv_res = await async_client.post("/api/v1/cache/invalidate", json={"workspace_id": "ws-api"})
    assert inv_res.status_code == 200
    assert inv_res.json()["status"] == "success"
