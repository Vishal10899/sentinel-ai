"""Production-grade Unit and Integration tests for Task 09–10 — Enterprise Identity & Audit Layer (RBAC + Audit Logs)."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.api.dependencies import current_user
from app.audit.engine import AuditEngine, audit_engine
from app.audit.exporter import AuditExporter, audit_exporter
from app.audit.repository import AuditRepository, audit_repository
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.rbac.engine import RBACEngine, rbac_engine
from app.rbac.repository import RoleRepository, role_repository

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


async def override_current_user():
    return User(
        id="audituser123",
        name="Audit User",
        email="audit@sentinel.ai",
        salt="auditsalt123",
        password_hash="audithash123",
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
            id="audituser123",
            name="Audit User",
            email="audit@sentinel.ai",
            salt="auditsalt123",
            password_hash="audithash123",
        )
        db.add(user)
        workspace = Workspace(
            id="audit-workspace-uuid",
            name="Audit Workspace",
            slug="audit-workspace",
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
async def test_builtin_roles_and_permission_checking():
    """Verify built-in enterprise roles and RBACEngine permission evaluation."""
    engine = RBACEngine(repository=role_repository)
    role_repository.assign_user_role("user-admin", "role-super-admin")

    # Platform Admin has wildcard permission
    assert engine.check_permission("user-admin", "provider.manage") is True
    assert engine.check_permission("user-admin", "random.permission") is True

    # Test custom user role assignment
    role_repository.assign_user_role("user-dev", "role-developer")

    # Developer role permissions
    assert engine.check_permission("user-dev", "chat.write") is True
    assert engine.check_permission("user-dev", "roles.manage") is False  # Restricted


@pytest.mark.asyncio
async def test_custom_role_creation_and_management():
    """Verify custom role creation, updating permissions, and deletion."""
    repo = RoleRepository()

    # Create custom role
    role = repo.create_role(
        name="Security Compliance Auditor",
        description="Auditor role for SOC 2 audits.",
        permissions=["audit.read", "audit.export"],
    )
    assert role.name == "Security Compliance Auditor"
    assert role.is_builtin is False
    assert role.has_permission("audit.read") is True
    assert role.has_permission("provider.manage") is False

    # Update role
    updated = repo.update_role(role.id, permissions=["audit.read", "audit.export", "analytics.read"])
    assert updated is not None
    assert "analytics.read" in updated.permissions

    # Delete custom role
    deleted = repo.delete_role(role.id)
    assert deleted is True


@pytest.mark.asyncio
async def test_audit_event_logging_and_search():
    """Verify immutable audit event recording and multi-criteria search filtering."""
    engine = AuditEngine(repository=audit_repository)

    # Record audit events
    engine.record_event(action="USER_LOGIN", resource="auth/login", user_id="u1", user_name="Alice", workspace_id="ws-100")
    engine.record_event(action="POLICY_UPDATE", resource="policies/p1", user_id="u1", user_name="Alice", workspace_id="ws-100", severity="WARNING")
    engine.record_event(action="GUARDRAIL_BLOCK", resource="chat/stream", user_id="u2", user_name="Bob", workspace_id="ws-100", severity="CRITICAL")

    # Search audit logs
    records_ws = audit_repository.search(workspace_id="ws-100")
    assert len(records_ws) >= 3

    records_critical = audit_repository.search(workspace_id="ws-100", severity="CRITICAL")
    assert len(records_critical) >= 1
    assert records_critical[0].action == "GUARDRAIL_BLOCK"


@pytest.mark.asyncio
async def test_audit_export_csv_and_json():
    """Verify AuditExporter generating clean CSV and JSON export strings."""
    engine = AuditEngine(repository=audit_repository)
    rec = engine.record_event(action="KEY_ROTATE", resource="virtual-keys/k1", user_name="Charlie")

    exporter = AuditExporter()

    # JSON export
    json_out = exporter.export_json([rec])
    assert "KEY_ROTATE" in json_out
    assert "Charlie" in json_out

    # CSV export
    csv_out = exporter.export_csv([rec])
    assert "KEY_ROTATE" in csv_out
    assert "Timestamp" in csv_out  # Header present


@pytest.mark.asyncio
async def test_roles_and_audit_rest_api_endpoints(async_client: AsyncClient):
    """Test Roles and Audit REST API endpoints."""
    # 1. List Roles API
    roles_res = await async_client.get("/api/v1/roles")
    assert roles_res.status_code == 200
    assert len(roles_res.json()) >= 5

    # 2. Permission Matrix API
    matrix_res = await async_client.get("/api/v1/roles/permissions/matrix")
    assert matrix_res.status_code == 200
    assert "all_permissions" in matrix_res.json()

    # 3. Create Custom Role API
    create_role_res = await async_client.post("/api/v1/roles", json={
        "name": "Integration Test Role",
        "description": "Role for integration testing",
        "permissions": ["chat.read", "analytics.read"],
    })
    assert create_role_res.status_code == 201
    role_id = create_role_res.json()["id"]

    # 4. Search Audit Logs API
    audit_search_res = await async_client.get("/api/v1/audit")
    assert audit_search_res.status_code == 200
    assert isinstance(audit_search_res.json(), list)

    # 5. Audit Stats API
    audit_stats_res = await async_client.get("/api/v1/audit/stats")
    assert audit_stats_res.status_code == 200
    assert "total_audit_events" in audit_stats_res.json()

    # 6. Audit Export CSV API
    export_csv_res = await async_client.get("/api/v1/audit/export?format=csv")
    assert export_csv_res.status_code == 200
    assert "text/csv" in export_csv_res.headers["content-type"]

    # 7. Audit Export JSON API
    export_json_res = await async_client.get("/api/v1/audit/export?format=json")
    assert export_json_res.status_code == 200
    assert "application/json" in export_json_res.headers["content-type"]
