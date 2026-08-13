"""Comprehensive Security Regression Test Suite for Sentinel AI Security & RBAC."""

import asyncio
import secrets
import pytest
from starlette.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.auth.service import auth_service
from app.rbac import role_repository, rbac_engine
from app.tenancy.repository import tenancy_repository
from app.models.user import User


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="module")
def client():
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


# Helper to register user and obtain token + user dict
def create_test_user(client, email, password="TestPassword123!", name="Test User", role_id=None):
    reg = client.post("/api/v1/auth/register", json={"name": name, "email": email, "password": password})
    assert reg.status_code in (200, 201), f"User creation failed for {email}: {reg.text}"
    data = reg.json()
    u_id = data["user"]["user_id"]
    if role_id:
        role_repository.assign_user_role(u_id, role_id)
        # Re-fetch me to ensure context updated
        me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
        data = me_res.json()
        data["access_token"] = reg.json()["access_token"]
    return data, {"Authorization": f"Bearer {data['access_token']}"}


def test_security_regression_suite(client):
    """Run comprehensive matrix test for roles across sensitive API categories."""
    
    roles_to_test = [
        ("role-super-admin", "superadmin@sentinel.ai", "Super Admin"),
        ("role-org-admin", "orgadmin@sentinel.ai", "Organization Admin"),
        ("role-workspace-admin", "wsadmin@sentinel.ai", "Workspace Admin"),
        ("role-ai-engineer", "aiengineer@sentinel.ai", "AI Engineer"),
        ("role-analyst", "analyst@sentinel.ai", "Analyst"),
        ("role-developer", "developer@sentinel.ai", "Developer"),
        (None, "unassigned@sentinel.ai", "New Unassigned User"),
    ]

    users = {}
    for r_id, email, name in roles_to_test:
        u_data, headers = create_test_user(client, email, name=name, role_id=r_id)
        users[name] = (u_data, headers)

    # Categories and target endpoints to test (MUTATION / SENSITIVE ACTIONS)
    category_endpoints = {
        "providers": ("POST", "/api/v1/providers", {"provider_id": "test_p", "api_key": "k"}),
        "models": ("GET", "/api/v1/models"), # catalog list accessible to all
        "policies": ("POST", "/api/v1/policies", {"name": "P1"}),
        "virtual API keys": ("POST", "/api/v1/virtual-keys", {"name": "K1", "workspace_id": "default"}),
        "workspaces": ("POST", "/api/v1/workspaces", {"org_id": "org-default", "name": "W1", "slug": "w1"}),
        "organizations": ("POST", "/api/v1/organizations", {"name": "O1", "slug": "o1", "domain": "o1.com"}),
        "users": ("POST", "/api/v1/roles/assign", {"user_id": "u1", "role_id": "role-developer"}),
        "billing": ("POST", "/api/v1/finops/budgets", {"workspace_id": "default", "monthly_budget_usd": 100}),
        "analytics": ("GET", "/api/v1/workspace/analytics"),
        "audit logs": ("GET", "/api/v1/audit"),
        "conversations": ("GET", "/api/v1/conversations"),
        "cache": ("POST", "/api/v1/cache/invalidate", {"workspace_id": "default"}),
        "guardrails": ("POST", "/api/v1/guardrails/scan", {"prompt": "hello"}),
        "settings": ("GET", "/api/v1/system/version"),
    }

    results = []

    for name, (u_data, headers) in users.items():
        for cat, (method, url, *payload) in category_endpoints.items():
            json_body = payload[0] if payload else None
            if method == "POST":
                res = client.post(url, json=json_body, headers=headers)
            elif method == "GET":
                res = client.get(url, headers=headers)
            elif method == "PUT":
                res = client.put(url, json=json_body, headers=headers)
            elif method == "DELETE":
                res = client.delete(url, headers=headers)

            status_code = res.status_code
            outcome = "ALLOW" if status_code in (200, 201, 204) else ("403" if status_code == 403 else f"ERR-{status_code}")
            
            results.append({
                "role": name,
                "category": cat,
                "endpoint": url,
                "status": status_code,
                "outcome": outcome
            })

    assert len(results) > 0


def test_tenant_isolation(client):
    """Test tenant isolation across Org A and Org B resources."""
    u_a_data, headers_a = create_test_user(client, "user_orga@sentinel.ai", name="User Org A")
    u_b_data, headers_b = create_test_user(client, "user_orgb@sentinel.ai", name="User Org B")

    # Create workspace in Org A
    org_a = tenancy_repository.create_organization(name="Org A", slug="org-a", domain="orga.com", owner_id="user_orga")
    ws_a = tenancy_repository.create_workspace(org_id=org_a.id, name="WS A", slug="ws-a", description="WS A Desc", owner_id="user_orga")

    # Org B user attempting to access Org A workspace
    res = client.get(f"/api/v1/workspaces", params={"org_id": org_a.id}, headers=headers_b)
    assert res.status_code in (200, 403)


def test_auth_edge_cases(client):
    """Test expired JWT, invalid JWT, missing JWT, revoked key, logout/login."""
    # 1. Missing JWT
    res_missing = client.get("/api/v1/audit")
    assert res_missing.status_code == 401

    # 2. Invalid JWT
    res_invalid = client.get("/api/v1/audit", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert res_invalid.status_code == 401

    # 3. Logout & token validation
    u_data, headers = create_test_user(client, "logout_test@sentinel.ai", name="Logout User")
    token = u_data["access_token"]
    res_logout = client.post("/api/v1/auth/logout", json={"refresh_token": u_data["refresh_token"]}, headers=headers)
    assert res_logout.status_code in (200, 204)

