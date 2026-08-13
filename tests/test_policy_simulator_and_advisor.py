"""Production-grade Unit and Integration tests for Task 19–20 — Policy Simulator & AI Optimization Advisor."""

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
from app.simulation.advisor import OptimizationAdvisor, optimization_advisor
from app.simulation.engine import PolicySimulator, PolicyVersionManager, policy_simulator, policy_version_manager

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


async def override_current_user():
    return User(
        id="simuser123",
        name="Simulator User",
        email="sim@sentinel.ai",
        salt="simsalt123",
        password_hash="simhash123",
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
            id="simuser123",
            name="Simulator User",
            email="sim@sentinel.ai",
            salt="simsalt123",
            password_hash="simhash123",
        )
        db.add(user)
        workspace = Workspace(
            id="sim-workspace-uuid",
            name="Simulator Workspace",
            slug="sim-workspace",
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
async def test_policy_simulator_dry_run_analysis():
    """Verify dry-run simulation execution and impact analysis calculation."""
    simulator = PolicySimulator()

    proposed_policy = {
        "max_cost_per_request": 0.001,
        "blocked_models": ["gpt-4o"],
    }

    res = simulator.simulate(
        proposed_policy=proposed_policy,
        workspace_id="default",
        user_id="sim-admin",
        sample_size=20,
    )

    assert res.total_requests >= 1
    assert res.blocked_count >= 0
    assert isinstance(res.impact_percentage, float)

    # Check audit event emission
    audit_logs = audit_repository.search(action="SIMULATION_EXECUTED")
    assert len(audit_logs) >= 1


@pytest.mark.asyncio
async def test_policy_versioning_and_rollback():
    """Verify policy version publishing, active version switching, and zero-downtime rollback."""
    mgr = PolicyVersionManager()

    # Publish v1.1
    v1_1 = mgr.publish_version({"max_cost_per_request": 0.08}, publisher="admin-alice")
    assert v1_1.version_number == "v1.1"
    assert v1_1.is_active is True

    # Rollback to v1.0
    v1_0 = mgr.rollback_version("ver-v1.0", actor="admin-alice")
    assert v1_0 is not None
    assert v1_0.is_active is True
    assert v1_1.is_active is False

    # Check audit event emission
    audit_logs = audit_repository.search(action="POLICY_ROLLED_BACK")
    assert len(audit_logs) >= 1


@pytest.mark.asyncio
async def test_optimization_advisor_recommendations():
    """Verify AI optimization recommendation generation and application."""
    advisor = OptimizationAdvisor()

    recs = advisor.get_recommendations()
    assert len(recs) >= 3

    # Apply recommendation
    applied = advisor.apply_recommendation(recs[0].id, actor_id="admin-bob")
    assert applied is not None
    assert applied.status == "APPLIED"

    # Check audit log emission
    audit_logs = audit_repository.search(action="OPTIMIZATION_ACCEPTED")
    assert len(audit_logs) >= 1


@pytest.mark.asyncio
async def test_policy_simulator_rest_api_endpoints(async_client: AsyncClient):
    """Test Policy Simulator & Optimization Advisor REST API endpoints."""
    # 1. POST Run Simulation API
    sim_res = await async_client.post("/api/v1/policies/simulation/run", json={
        "workspace_id": "default",
        "proposed_policy": {"max_cost_per_request": 0.05, "blocked_models": ["claude-3-5-sonnet"]},
        "sample_trace_count": 50,
    })
    assert sim_res.status_code == 200
    assert "impact_percentage" in sim_res.json()

    # 2. GET List Versions API
    ver_res = await async_client.get("/api/v1/policies/simulation/versions")
    assert ver_res.status_code == 200
    assert len(ver_res.json()) >= 1

    # 3. POST Publish Version API
    pub_res = await async_client.post("/api/v1/policies/simulation/versions", json={
        "policy_data": {"max_cost_per_request": 0.03},
        "published_by": "api-user",
    })
    assert pub_res.status_code == 201
    pub_ver_id = pub_res.json()["version_id"]

    # 4. POST Rollback API
    roll_res = await async_client.post(f"/api/v1/policies/simulation/versions/{pub_ver_id}/rollback")
    assert roll_res.status_code == 200
    assert roll_res.json()["is_active"] is True

    # 5. GET Recommendations API
    rec_res = await async_client.get("/api/v1/policies/simulation/advisor/recommendations")
    assert rec_res.status_code == 200
    assert len(rec_res.json()) >= 1
    rec_id = rec_res.json()[0]["id"]

    # 6. POST Apply Recommendation API
    apply_res = await async_client.post(f"/api/v1/policies/simulation/advisor/recommendations/{rec_id}/apply")
    assert apply_res.status_code == 200
    assert apply_res.json()["status"] == "APPLIED"

    # 7. POST What-If Scenario API
    what_if_res = await async_client.post("/api/v1/policies/simulation/what-if", json={
        "scenario_type": "DISABLE_MODEL",
        "parameters": {"model_id": "gpt-4o"},
    })
    assert what_if_res.status_code == 200
    assert "explanation" in what_if_res.json()
    assert what_if_res.json()["scenario_name"] == "DISABLE_MODEL"
