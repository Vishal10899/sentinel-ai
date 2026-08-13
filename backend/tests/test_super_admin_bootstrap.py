"""Comprehensive Super Admin Bootstrap and Security Test Suite."""

import asyncio
import pytest
from starlette.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.settings import settings
from app.rbac import role_repository
from app.tenancy.repository import tenancy_repository


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
def test_client():
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


def test_scenario_a_super_admin_vishal_kumar(test_client):
    """Scenario A: Vishalkumar75912@gmail.com platform-level Super Admin."""
    email = "Vishalkumar75912@gmail.com"
    password = "SuperAdminPassword123!"

    # 1. Register or login
    reg = test_client.post("/api/v1/auth/register", json={
        "name": "Vishal Kumar",
        "email": email,
        "password": password,
    })
    assert reg.status_code in (200, 201), f"Register failed: {reg.text}"
    data = reg.json()
    assert data["role"]["id"] == "role-super-admin"
    assert "*" in data["permissions"]
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Verify /auth/me
    me_res = test_client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["user"]["email"] == email.lower()
    assert me_data["role"]["name"] == "Super Admin"
    assert "*" in me_data["permissions"]
    assert "password" not in me_data["user"]
    assert "password_hash" not in me_data["user"]
    assert "salt" not in me_data["user"]

    # 3. Verify privileged actions
    # audit.read
    audit_res = test_client.get("/api/v1/audit", headers=headers)
    assert audit_res.status_code == 200

    # users.manage / role assignment
    assign_res = test_client.post("/api/v1/roles/assign", json={
        "user_id": "test_user_target",
        "role_id": "role-developer",
    }, headers=headers)
    assert assign_res.status_code in (200, 201)

    # provider.manage
    prov_res = test_client.get("/api/v1/providers", headers=headers)
    assert prov_res.status_code == 200

    # model.manage / catalog
    model_res = test_client.get("/api/v1/models", headers=headers)
    assert model_res.status_code == 200

    # policy.manage
    pol_res = test_client.get("/api/v1/policies", headers=headers)
    assert pol_res.status_code == 200

    # platform organizations access
    orgs_res = test_client.get("/api/v1/organizations", headers=headers)
    assert orgs_res.status_code == 200

    # platform workspaces access
    ws_res = test_client.get("/api/v1/workspaces", headers=headers)
    assert ws_res.status_code == 200


def test_scenario_b_super_admin_founder_vishal_chaudhary(test_client):
    """Scenario B: Vishalchaudhary74096@gmail.com platform-level Super Admin (Founder)."""
    email = "Vishalchaudhary74096@gmail.com"
    password = "FounderPassword123!"

    # 1. Register or login
    reg = test_client.post("/api/v1/auth/register", json={
        "name": "Vishal Chaudhary",
        "email": email,
        "password": password,
    })
    assert reg.status_code in (200, 201), f"Register failed: {reg.text}"
    data = reg.json()
    assert data["role"]["id"] == "role-super-admin"
    assert "*" in data["permissions"]
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Verify /auth/me with Founder display
    me_res = test_client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["user"]["email"] == email.lower()
    assert me_data["role"]["name"] == "Super Admin"
    assert "*" in me_data["permissions"]
    assert me_data["user"].get("title") == "Founder"

    # 3. Verify privileged actions
    assert test_client.get("/api/v1/audit", headers=headers).status_code == 200
    assert test_client.get("/api/v1/providers", headers=headers).status_code == 200
    assert test_client.get("/api/v1/policies", headers=headers).status_code == 200
    assert test_client.get("/api/v1/virtual-keys", headers=headers).status_code == 200
    assert test_client.get("/api/v1/organizations", headers=headers).status_code == 200


def test_scenario_c_normal_customer_signup_not_super_admin(test_client):
    """Scenario C: Public customer signup does NOT get Super Admin privileges."""
    email = "new_customer_ceo@acme.com"
    password = "AcmePassword123!"

    reg = test_client.post("/api/v1/auth/register", json={
        "name": "Acme CEO",
        "email": email,
        "password": password,
    })
    assert reg.status_code in (200, 201)
    data = reg.json()

    # Must be Organization Admin for Acme Org, NOT platform Super Admin
    assert data["role"]["id"] == "role-org-admin"
    assert "*" not in data["permissions"]
    assert data["organization"]["owner_id"] == data["user"]["user_id"]
    assert data["is_owner"] is True


def test_scenario_d_organization_admin_tenant_boundary(test_client):
    """Scenario D: Org A admin cannot access Org B resources."""
    # Org A creation
    reg_a = test_client.post("/api/v1/auth/register", json={
        "name": "Org A Admin",
        "email": "admin@org-a.com",
        "password": "PasswordA123!",
    })
    token_a = reg_a.json()["access_token"]
    org_a_id = reg_a.json()["organization"]["id"]

    # Org B creation
    reg_b = test_client.post("/api/v1/auth/register", json={
        "name": "Org B Admin",
        "email": "admin@org-b.com",
        "password": "PasswordB123!",
    })
    token_b = reg_b.json()["access_token"]
    org_b_id = reg_b.json()["organization"]["id"]

    # Org B admin trying to view Org A details
    res = test_client.get(f"/api/v1/organizations/{org_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 403
    assert "Cross-tenant access denied" in res.json()["detail"]

    # Org B admin trying to list Org A members
    res_mem = test_client.get(f"/api/v1/organizations/{org_a_id}/members", headers={"Authorization": f"Bearer {token_b}"})
    assert res_mem.status_code == 403


def test_scenario_e_developer_restricted_from_admin_apis(test_client):
    """Scenario E: Developer joining via invite is restricted from Super Admin/Org Admin endpoints."""
    # Issue invitation for developer
    inv = tenancy_repository.create_invitation(
        org_id="org-default",
        workspace_id="default",
        email="dev_restricted@sentinel.ai",
        role_id="role-developer",
    )

    reg = test_client.post("/api/v1/auth/register", json={
        "name": "Restricted Dev",
        "email": "dev_restricted@sentinel.ai",
        "password": "DevPassword123!",
    })
    assert reg.status_code in (200, 201)
    data = reg.json()
    assert data["role"]["id"] == "role-developer"
    assert "*" not in data["permissions"]

    headers = {"Authorization": f"Bearer {data['access_token']}"}

    # Cannot read audit logs
    assert test_client.get("/api/v1/audit", headers=headers).status_code == 403

    # Cannot modify providers
    assert test_client.post("/api/v1/providers", json={"provider_id": "p", "api_key": "k"}, headers=headers).status_code == 403

    # Cannot assign roles
    assert test_client.post("/api/v1/roles/assign", json={"user_id": "u", "role_id": "role-super-admin"}, headers=headers).status_code == 403


def test_scenario_f_security_no_passwords_or_hashes_exposed(test_client):
    """Scenario F: Passwords and hashes are never exposed through auth endpoints."""
    reg = test_client.post("/api/v1/auth/register", json={
        "name": "Security Test User",
        "email": "security_test@sentinel.ai",
        "password": "SecurePassword123!",
    })
    assert reg.status_code in (200, 201)
    body = reg.text

    assert "SecurePassword123!" not in body
    assert "password_hash" not in body
    assert "salt" not in body

    # /auth/me check
    token = reg.json()["access_token"]
    me_res = test_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    me_body = me_res.text
    assert "SecurePassword123!" not in me_body
    assert "password_hash" not in me_body
    assert "salt" not in me_body
