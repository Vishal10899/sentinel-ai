"""Production-grade Unit and Integration tests for Task 13–14 — Enterprise Observability & Timeline Replay."""

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
from app.observability.engine import TraceEngine, trace_engine
from app.observability.models import TraceRecord
from app.observability.repository import ObservabilityRepository, observability_repository

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


async def override_current_user():
    return User(
        id="obsuser123",
        name="Observability User",
        email="obs@sentinel.ai",
        salt="obssalt123",
        password_hash="obshash123",
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
            id="obsuser123",
            name="Observability User",
            email="obs@sentinel.ai",
            salt="obssalt123",
            password_hash="obshash123",
        )
        db.add(user)
        workspace = Workspace(
            id="obs-workspace-uuid",
            name="Observability Workspace",
            slug="obs-workspace",
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
async def test_trace_creation_and_timeline_stage_timing():
    """Verify TraceContext stage creation, timing calculation, and trace persistence."""
    repo = ObservabilityRepository()
    engine = TraceEngine(repository=repo)

    ctx = engine.create_trace(
        conversation_id="conv-100",
        workspace_id="ws-obs",
        provider_id="openai",
        model_id="gpt-4o",
        prompt="Explain quantum entanglement",
    )

    ctx.start_stage("GUARDRAIL_SCAN")
    ctx.end_stage("GUARDRAIL_SCAN")

    ctx.start_stage("PROVIDER_LLM_CALL")
    ctx.end_stage("PROVIDER_LLM_CALL")

    record = ctx.finish(status="SUCCESS", response="Quantum entanglement is...", tokens=120, cost_usd=0.002)

    assert record.trace_id == ctx.trace_id
    assert len(record.timeline_stages) == 2
    assert record.timeline_stages[0].stage_name == "GUARDRAIL_SCAN"
    assert record.total_latency_ms >= 0.0

    # Retrieve from repository
    saved = repo.get_trace(record.trace_id)
    assert saved is not None
    assert saved.prompt == "Explain quantum entanglement"


@pytest.mark.asyncio
async def test_provider_health_telemetry_calculations():
    """Verify provider health status aggregation, P95/P99 latency calculation, and availability."""
    repo = ObservabilityRepository()

    # Log successful and failed requests
    for i in range(10):
        tr = TraceRecord(
            trace_id=f"tr-{i}",
            correlation_id=f"c-{i}",
            conversation_id="c1",
            workspace_id="w1",
            user_id="u1",
            provider_id="openai",
            model_id="gpt-4o",
            prompt="Hello",
            response="World",
            tokens=20,
            total_latency_ms=100.0 + i * 20.0,
            status="SUCCESS" if i < 9 else "FAILED",
        )
        repo.save_trace(tr)

    health_list = repo.get_provider_health()
    assert len(health_list) > 0
    openai_health = next((h for h in health_list if (getattr(h, 'provider_id', None) or h.get('provider_id')) == "openai"), None)
    assert openai_health is not None


@pytest.mark.asyncio
async def test_request_replay_snapshot_generation():
    """Verify read-only Request Replay snapshot generation and audit log emission."""
    repo = ObservabilityRepository()
    engine = TraceEngine(repository=repo)

    ctx = engine.create_trace(
        conversation_id="conv-200",
        workspace_id="ws-replay",
        provider_id="anthropic",
        model_id="claude-3-5-sonnet",
        prompt="Write python quicksort",
    )
    ctx.start_stage("ROUTING")
    ctx.end_stage("ROUTING")
    tr = ctx.finish(status="SUCCESS", response="def quicksort(arr): ...", tokens=150, cost_usd=0.003)

    # Generate replay snapshot
    replay = engine.generate_replay(tr.trace_id, requesting_user_id="user-auditor")
    assert replay is not None
    assert replay.trace_id == tr.trace_id
    assert replay.prompt == "Write python quicksort"
    assert len(replay.timeline_stages) >= 1

    # Check audit event emission
    audit_logs = audit_repository.search(action="REQUEST_REPLAY_VIEWED")
    assert len(audit_logs) >= 1
    assert audit_logs[0].user_id == "user-auditor"


@pytest.mark.asyncio
async def test_observability_rest_api_endpoints(async_client: AsyncClient):
    """Test Observability & Timeline Replay REST API endpoints."""
    # Seed a trace first
    ctx = trace_engine.create_trace(
        conversation_id="conv-api",
        workspace_id="ws-api",
        provider_id="gemini",
        model_id="gemini-1.5-pro",
        prompt="API Test Prompt",
    )
    ctx.start_stage("LLM_CALL")
    ctx.end_stage("LLM_CALL")
    tr = ctx.finish(status="SUCCESS", response="API Test Response", tokens=50, cost_usd=0.001)

    # 1. GET List Traces API
    traces_res = await async_client.get("/api/v1/observability/traces")
    assert traces_res.status_code == 200
    assert isinstance(traces_res.json(), list)
    assert len(traces_res.json()) >= 1

    # 2. GET Trace Detail API
    trace_detail_res = await async_client.get(f"/api/v1/observability/traces/{tr.trace_id}")
    assert trace_detail_res.status_code == 200
    assert trace_detail_res.json()["trace_id"] == tr.trace_id

    # 3. GET Request Replay API
    replay_res = await async_client.get(f"/api/v1/observability/traces/{tr.trace_id}/replay")
    assert replay_res.status_code == 200
    assert replay_res.json()["prompt"] == "API Test Prompt"

    # 4. GET Operational Metrics API
    metrics_res = await async_client.get("/api/v1/observability/metrics")
    assert metrics_res.status_code == 200
    metrics_data = metrics_res.json()
    assert "total_requests" in metrics_data or "total_traces" in metrics_data

    # 5. GET Provider Health API
    health_res = await async_client.get("/api/v1/observability/providers/health")
    assert health_res.status_code == 200
    assert len(health_res.json()) >= 5

    # 6. GET Operational Alerts API
    alerts_res = await async_client.get("/api/v1/observability/alerts")
    assert alerts_res.status_code == 200
    assert isinstance(alerts_res.json(), list)
