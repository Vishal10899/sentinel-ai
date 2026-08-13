"""End-to-End Verification Test Suite for Auth/RBAC Scenarios A - F."""

import asyncio
import pytest
from starlette.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.auth.service import auth_service
from app.rbac import rbac_engine, role_repository
from app.tenancy.repository import tenancy_repository
from app.core.settings import settings


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async def init_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init_tables())

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def _get_test_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


def test_scenario_a_bootstrap_admin_login(test_db):
    """SCENARIO A: Bootstrap admin login -> Super Admin -> full authorized context."""
    email = settings.bootstrap_admin_email
    password = settings.bootstrap_admin_password

    # Register bootstrap admin
    reg = test_db.post("/api/v1/auth/register", json={"name": "System Admin", "email": email, "password": password})
    assert reg.status_code in (200, 201), f"Register failed: {reg.text}"
    
    res = test_db.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    data = res.json()
    assert data["role"]["id"] == "role-super-admin"
    assert "*" in data["permissions"]

    # Verify /auth/me
    token = data["access_token"]
    me_res = test_db.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["role"]["name"] == "Super Admin"
    assert "*" in me_data["permissions"]


def test_scenario_b_new_normal_signup(test_db):
    """SCENARIO B: New normal signup -> restricted default role -> no administrative privileges."""
    email = "user_b_normal@sentinel.ai"
    password = "UserPassword123!"

    reg = test_db.post("/api/v1/auth/register", json={"name": "Normal User B", "email": email, "password": password})
    assert reg.status_code in (200, 201), f"Signup failed: {reg.text}"
    data = reg.json()

    assert data["role"]["id"] in ("role-viewer", "role-developer")
    assert "*" not in data["permissions"]
    assert "provider.manage" not in data["permissions"]
    assert "rbac.manage" not in data["permissions"]
    assert "users.manage" not in data["permissions"]



def test_scenario_c_organization_employee_role(test_db):
    """SCENARIO C: Organization employee -> assigned workspace -> assigned role -> role permissions only."""
    email = "employee_c@sentinel.ai"
    password = "EmployeePassword123!"

    reg = test_db.post("/api/v1/auth/register", json={"name": "Employee C", "email": email, "password": password})
    assert reg.status_code in (200, 201)
    token = reg.json()["access_token"]
    user_id = reg.json()["user"]["user_id"]

    # Assign AI Engineer role
    assigned = role_repository.assign_user_role(user_id, "role-ai-engineer")
    assert assigned is True

    # Check effective permissions via API
    perm_res = test_db.get(f"/api/v1/roles/users/{user_id}/permissions", headers={"Authorization": f"Bearer {token}"})
    assert perm_res.status_code == 200
    perm_data = perm_res.json()

    assert perm_data["role"]["id"] == "role-ai-engineer"
    assert "chat.read" in perm_data["effective_permissions"]
    assert "analytics.read" in perm_data["effective_permissions"]
    assert "users.manage" not in perm_data["effective_permissions"]




def test_scenario_d_normal_user_admin_api_returns_403(test_db):
    """SCENARIO D: Normal user manually calls admin API -> 403 Forbidden."""
    # Register and login normal user
    reg = test_db.post("/api/v1/auth/register", json={"name": "Normal User D", "email": "user_d@sentinel.ai", "password": "UserPassword123!"})
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt provider modification (admin endpoint requiring provider.manage)
    res = test_db.post("/api/v1/providers", json={"provider_id": "custom_hack", "api_key": "hack"}, headers=headers)
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
    assert "Permission denied" in res.json()["detail"]

    # Attempt role assignment (admin endpoint requiring users.manage)
    res2 = test_db.post("/api/v1/roles/assign", json={"user_id": "some_id", "role_id": "role-super-admin"}, headers=headers)
    assert res2.status_code == 403, f"Expected 403, got {res2.status_code}: {res2.text}"


def test_scenario_e_admin_calls_same_api_succeeds(test_db):
    """SCENARIO E: Admin calls same admin API -> Success."""
    # Register and login admin
    email = settings.bootstrap_admin_email
    password = settings.bootstrap_admin_password
    reg = test_db.post("/api/v1/auth/register", json={"name": "Admin E", "email": email, "password": password})
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Call admin API (audit read)
    res = test_db.get("/api/v1/audit", headers=headers)
    assert res.status_code == 200, f"Admin call failed: {res.text}"
    assert isinstance(res.json(), list)


def test_scenario_f_cross_tenant_access_denied(test_db):
    """SCENARIO F: User attempts another organization's resource -> denied."""
    reg = test_db.post("/api/v1/auth/register", json={"name": "Normal User F", "email": "user_f@sentinel.ai", "password": "UserPassword123!"})
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to create workspace in unassigned org (requires workspace.manage permission)
    res = test_db.post("/api/v1/workspaces", json={"org_id": "other_org_99", "name": "Hack Workspace", "slug": "hack-ws"}, headers=headers)
    assert res.status_code == 403, f"Expected 403 for cross tenant access without permission, got {res.status_code}: {res.text}"
