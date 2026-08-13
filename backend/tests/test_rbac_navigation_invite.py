"""Unit and Integration tests for Strict RBAC UI Lockdown, Route Guards & Team Invite Flow."""

import asyncio
import pytest
from starlette.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.user import UserRole
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


def test_first_user_bootstrap_receives_admin_role(test_db):
    """Verify that the very first registered user receives ADMIN role."""
    reg_payload = {
        "name": "Workspace Admin",
        "email": settings.bootstrap_admin_email,
        "password": "AdminSecretPassword123!",
    }
    reg_res = test_db.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code in (200, 201), f"First user registration failed: {reg_res.text}"
    
    data = reg_res.json()
    assert data["user"]["role"] == UserRole.ADMIN or data["user"]["role"] == "ADMIN"
    
    # Verify token access
    token = data["access_token"]
    me_res = test_db.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["user"]["role"] == "ADMIN"


def test_team_invite_endpoint_admin_success(test_db):
    """Verify Admin can successfully send team invitations."""
    # 1. Register admin first
    admin_payload = {
        "name": "Admin User",
        "email": settings.bootstrap_admin_email,
        "password": "AdminPassword123!",
    }
    admin_reg = test_db.post("/api/v1/auth/register", json=admin_payload)
    token = admin_reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Invite developer team member
    invite_payload = {
        "email": "dev.user@company.com",
        "role": "DEVELOPER"
    }
    invite_res = test_db.post("/api/v1/team/invite", json=invite_payload, headers=headers)
    assert invite_res.status_code == 201, f"Invite failed: {invite_res.text}"
    inv_data = invite_res.json()
    assert inv_data["email"] == "dev.user@company.com"
    assert inv_data["role"] == "DEVELOPER"
    assert "invite_token" in inv_data


def test_developer_role_blocked_on_team_invite_and_providers(test_db):
    """Verify DEVELOPER role cannot send team invites or access provider settings (403 Forbidden)."""
    # 1. Bootstrap admin
    admin_payload = {
        "name": "Bootstrap Admin",
        "email": settings.bootstrap_admin_email,
        "password": "AdminPassword123!",
    }
    test_db.post("/api/v1/auth/register", json=admin_payload)

    # 2. Subsequent registration receives DEVELOPER role
    dev_payload = {
        "name": "Developer Bob",
        "email": "bob.developer@company.com",
        "password": "DevPassword123!",
        "role": "DEVELOPER",
    }
    dev_reg = test_db.post("/api/v1/auth/register", json=dev_payload)
    assert dev_reg.status_code in (200, 201)
    dev_data = dev_reg.json()
    assert dev_data["user"]["role"] in ("DEVELOPER", "MEMBER")

    dev_token = dev_data["access_token"]
    dev_headers = {"Authorization": f"Bearer {dev_token}"}

    # 3. Developer attempts team invite -> 403 Forbidden
    invite_res = test_db.post(
        "/api/v1/team/invite",
        json={"email": "hacker@company.com", "role": "ADMIN"},
        headers=dev_headers,
    )
    assert invite_res.status_code == 403
    assert "Only Workspace Admins can send team invitations." in invite_res.json()["detail"]

    # 4. Developer attempts provider access -> 403 Forbidden
    providers_res = test_db.get("/api/v1/providers", headers=dev_headers)
    assert providers_res.status_code == 403
