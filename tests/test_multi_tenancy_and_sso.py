"""Production-grade Unit and Integration tests for Task 15–16 — Enterprise Multi-Tenant Workspaces & SSO."""

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
from app.tenancy.engine import TenancyEngine, tenancy_engine
from app.tenancy.repository import TenancyRepository, tenancy_repository

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


async def override_current_user():
    return User(
        id="tenantuser123",
        name="Tenant User",
        email="tenant@sentinel.ai",
        salt="tenantsalt123",
        password_hash="tenanthash123",
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
            id="tenantuser123",
            name="Tenant User",
            email="tenant@sentinel.ai",
            salt="tenantsalt123",
            password_hash="tenanthash123",
        )
        db.add(user)
        workspace = Workspace(
            id="tenant-workspace-uuid",
            name="Tenant Workspace",
            slug="tenant-workspace",
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
async def test_organization_and_workspace_creation():
    """Verify Organization and Workspace creation and tenant scoping."""
    repo = TenancyRepository()
    engine = TenancyEngine(repository=repo)

    org = engine.create_organization(
        name="Acme Corporation",
        slug="acme-corp",
        domain="acme.com",
        owner_id="user-acme-owner",
    )
    assert org.name == "Acme Corporation"
    assert org.domain == "acme.com"

    # Workspace auto-created
    workspaces = repo.list_workspaces(org_id=org.id)
    assert len(workspaces) >= 1
    assert "Main Workspace" in workspaces[0].name

    # Create additional isolated workspace
    ws2 = engine.create_workspace(
        org_id=org.id,
        name="Acme R&D Lab",
        slug="rd-lab",
        description="Research & Development Workspace",
        owner_id="user-acme-owner",
    )
    assert ws2.org_id == org.id
    assert len(repo.list_workspaces(org_id=org.id)) == 2


@pytest.mark.asyncio
async def test_member_invitation_and_acceptance():
    """Verify invitation token generation, audit log emission, and token acceptance."""
    repo = TenancyRepository()
    engine = TenancyEngine(repository=repo)

    org = repo.create_organization("Beta Inc", "beta", "beta.io", "owner-beta")
    ws = repo.list_workspaces(org.id)[0]

    # Invite member
    inv = engine.invite_member(
        org_id=org.id,
        workspace_id=ws.id,
        email="developer@beta.io",
        role_id="role-developer",
        inviter_user_id="owner-beta",
    )
    assert inv.status == "PENDING"
    assert len(inv.token) >= 16

    # Verify audit event emission
    audit_logs = audit_repository.search(action="MEMBER_INVITED")
    assert len(audit_logs) >= 1

    # Accept invitation
    mem = repo.accept_invitation(token=inv.token, user_id="user-dev-beta")
    assert mem is not None
    assert mem.user_id == "user-dev-beta"
    assert mem.org_id == org.id


@pytest.mark.asyncio
async def test_enterprise_sso_provider_configuration():
    """Verify SAML / OIDC SSO identity provider configuration abstraction."""
    repo = TenancyRepository()
    engine = TenancyEngine(repository=repo)

    org = repo.create_organization("Enterprise Tech", "ent-tech", "ent.com", "owner-ent")

    # Configure Okta SAML Provider
    sso = engine.setup_sso(
        org_id=org.id,
        provider_type="OKTA",
        issuer_url="https://ent.okta.com",
        client_id="okta-client-123",
        actor_id="owner-ent",
    )
    assert sso.provider_type == "OKTA"
    assert sso.is_active is True

    # Retrieve SSO Provider
    fetched = repo.get_sso_provider(org.id)
    assert fetched is not None
    assert fetched.client_id == "okta-client-123"


@pytest.mark.asyncio
async def test_user_profile_management():
    """Verify user directory profile and preference management."""
    repo = TenancyRepository()

    prof = repo.get_or_create_profile(user_id="u-prof-1", display_name="Alice Smith")
    assert prof.display_name == "Alice Smith"
    assert prof.timezone == "UTC"

    updated = repo.update_profile(user_id="u-prof-1", timezone="America/New_York", language="es")
    assert updated.timezone == "America/New_York"
    assert updated.language == "es"


@pytest.mark.asyncio
async def test_tenancy_and_sso_rest_api_endpoints(async_client: AsyncClient):
    """Test Tenancy, Workspace, Invitation, SSO, and User Profile REST API endpoints."""
    # 1. GET List Organizations API
    orgs_res = await async_client.get("/api/v1/organizations")
    assert orgs_res.status_code == 200
    assert len(orgs_res.json()) >= 1

    # 2. POST Create Organization API
    create_org_res = await async_client.post("/api/v1/organizations", json={
        "name": "Integration Org",
        "slug": "integration-org",
        "domain": "int.ai",
    })
    assert create_org_res.status_code == 201
    org_id = create_org_res.json()["id"]

    # 3. GET List Workspaces API
    ws_res = await async_client.get(f"/api/v1/workspaces?org_id={org_id}")
    assert ws_res.status_code == 200
    assert len(ws_res.json()) >= 1
    ws_id = ws_res.json()[0]["id"]

    # 4. POST Issue Invitation API
    inv_res = await async_client.post(f"/api/v1/organizations/{org_id}/invitations", json={
        "workspace_id": ws_id,
        "email": "testdev@int.ai",
        "role_id": "role-developer",
    })
    assert inv_res.status_code == 201
    inv_token = inv_res.json()["token"]

    # 5. POST Accept Invitation API
    accept_res = await async_client.post("/api/v1/invitations/accept", json={
        "token": inv_token,
    })
    assert accept_res.status_code == 200
    assert accept_res.json()["user_id"] == "tenantuser123"

    # 6. POST Configure SSO API
    sso_res = await async_client.post(f"/api/v1/organizations/{org_id}/sso", json={
        "provider_type": "AZURE_AD",
        "issuer_url": "https://login.microsoftonline.com/tenant-id",
        "client_id": "azure-client-uuid",
    })
    assert sso_res.status_code == 200
    assert sso_res.json()["provider_type"] == "AZURE_AD"

    # 7. GET User Profile API
    prof_res = await async_client.get("/api/v1/users/me/profile")
    assert prof_res.status_code == 200
    assert "display_name" in prof_res.json()
