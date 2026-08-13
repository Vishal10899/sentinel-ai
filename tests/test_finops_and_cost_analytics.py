"""Production-grade Unit and Integration tests for Task 11–12 — Enterprise Financial Governance & Cost Intelligence."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.api.dependencies import current_user
from app.db.base import Base
from app.db.session import get_db
from app.finops.analytics import CostAnalytics, CostForecast, CostOptimizer, cost_analytics, cost_forecast, cost_optimizer
from app.finops.engine import BudgetEngine, budget_engine
from app.finops.repository import FinOpsRepository, finops_repository
from app.models.user import User
from app.models.workspace import Workspace

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


async def override_current_user():
    return User(
        id="finuser123",
        name="FinOps User",
        email="fin@sentinel.ai",
        salt="finsalt123",
        password_hash="finhash123",
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
            id="finuser123",
            name="FinOps User",
            email="fin@sentinel.ai",
            salt="finsalt123",
            password_hash="finhash123",
        )
        db.add(user)
        workspace = Workspace(
            id="fin-workspace-uuid",
            name="FinOps Workspace",
            slug="fin-workspace",
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
async def test_budget_evaluation_and_threshold_alerts():
    """Verify high-performance BudgetEngine evaluation and threshold alert triggering."""
    repo = FinOpsRepository()
    engine = BudgetEngine(repository=repo)

    # Set up test budget of $100
    repo.update_budget("ws-fin-test", monthly_budget_usd=100.0, action_on_exceeded="REJECT")

    # Initial evaluation should allow
    res1 = engine.evaluate_request("ws-fin-test", estimated_cost=10.0)
    assert res1.allowed is True
    assert res1.status == "OK"

    # Record spend to reach $75 (75% threshold)
    repo.record_spend("ws-fin-test", "u1", "openai", "gpt-4o", 1000, 500, 75.0)

    # Evaluate again - should trigger 50% and 75% alerts
    res2 = engine.evaluate_request("ws-fin-test", estimated_cost=1.0)
    assert res2.allowed is True
    alerts = repo.list_alerts("ws-fin-test")
    assert len(alerts) >= 2

    # Record spend to reach $105 (exceed $100 budget)
    repo.record_spend("ws-fin-test", "u1", "openai", "gpt-4o", 1000, 500, 30.0)

    # Next request should be rejected with HTTP 403
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        engine.evaluate_request("ws-fin-test", estimated_cost=5.0)
    assert exc_info.value.status_code == 403
    assert "exceeded" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_cost_analytics_forecasting_and_optimizer():
    """Verify spend aggregation analytics, monthly forecast, and AI cost recommendations."""
    repo = FinOpsRepository()
    analytics = CostAnalytics(repository=repo)
    forecast = CostForecast(repository=repo)
    optimizer = CostOptimizer()

    repo.record_spend("ws-opt", "u1", "openai", "gpt-4o", 2000, 1000, 12.50)
    repo.record_spend("ws-opt", "u1", "anthropic", "claude-3-5-sonnet", 1500, 800, 8.20)

    # Spend summary
    summary = analytics.get_summary(workspace_id="ws-opt")
    assert summary.total_spend_usd == 20.70
    assert summary.total_requests == 2
    assert "openai" in summary.spend_by_provider
    assert "claude-3-5-sonnet" in summary.spend_by_model

    # Spend forecast
    fc = forecast.forecast_spend(workspace_id="ws-opt")
    assert fc["current_spend_usd"] == 20.70
    assert "projected_monthly_spend_usd" in fc

    # Cost optimizer recommendations
    recs = optimizer.generate_recommendations()
    assert len(recs) >= 3
    assert "savings_percentage" in recs[0]


@pytest.mark.asyncio
async def test_finops_rest_api_endpoints(async_client: AsyncClient):
    """Test FinOps REST API endpoints."""
    # 1. GET Budgets API
    budgets_res = await async_client.get("/api/v1/finops/budgets?workspace_id=default")
    assert budgets_res.status_code == 200
    assert "monthly_budget_usd" in budgets_res.json()

    # 2. POST Update Budget API
    update_budget_res = await async_client.post("/api/v1/finops/budgets", json={
        "workspace_id": "default",
        "monthly_budget_usd": 750.0,
        "action_on_exceeded": "WARN",
    })
    assert update_budget_res.status_code == 200
    assert update_budget_res.json()["monthly_budget_usd"] == 750.0

    # 3. GET Spend Analytics API
    spend_res = await async_client.get("/api/v1/finops/analytics/spend")
    assert spend_res.status_code == 200
    assert "total_spend_usd" in spend_res.json()

    # 4. GET Forecast API
    forecast_res = await async_client.get("/api/v1/finops/analytics/forecast")
    assert forecast_res.status_code == 200
    assert "projected_monthly_spend_usd" in forecast_res.json()

    # 5. GET Alerts API
    alerts_res = await async_client.get("/api/v1/finops/analytics/alerts")
    assert alerts_res.status_code == 200
    assert isinstance(alerts_res.json(), list)

    # 6. GET Recommendations API
    recs_res = await async_client.get("/api/v1/finops/analytics/optimization")
    assert recs_res.status_code == 200
    assert len(recs_res.json()) >= 1
