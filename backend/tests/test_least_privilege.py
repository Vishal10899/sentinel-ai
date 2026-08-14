"""Explicit Least-Privilege & Boundary Test Suite."""
import asyncio
import pytest
from starlette.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.auth.service import auth_service
from app.rbac import role_repository, rbac_engine
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
def _setup_user(client, email, role_id=None, name="Test User"):
    reg = client.post("/api/v1/auth/register", json={"name": name, "email": email, "password": "Password123!"})
    assert reg.status_code in (200, 201)
    data = reg.json()
    u_id = data["user"]["user_id"]
    if role_id:
        role_repository.assign_user_role(u_id, role_id)
        mems = tenancy_repository.list_members(org_id=None)
        user_mem = next((m for m in mems if m.user_id == u_id), None)
        if user_mem:
            user_mem.role_id = role_id
        from app.models.user import User
        user_obj = User(id=u_id, name=name, email=email, salt="salt", password_hash="hash")
        tokens = auth_service.token_pair(user_obj)
        data = tokens
    return data, {"Authorization": f"Bearer {data['access_token']}"}
def test_new_signup_is_org_admin(test_db):
    """1. New customer signup -> Organization Admin for new org (not platform super-admin)"""
    data, _ = _setup_user(test_db, "new_signup@sentinel.ai")
    assert data["role"]["id"] == "role-org-admin"
    assert "*" not in data["permissions"]
def test_viewer_cannot_create_api_key(test_db):
    """2. Viewer -> cannot create API key"""
    _, headers = _setup_user(test_db, "viewer1@sentinel.ai", role_id="role-viewer")
    res = test_db.post("/api/v1/virtual-keys", json={"name": "K1"}, headers=headers)
    assert res.status_code == 403
def test_viewer_cannot_invalidate_cache(test_db):
    """3. Viewer -> cannot invalidate cache"""
    _, headers = _setup_user(test_db, "viewer2@sentinel.ai", role_id="role-viewer")
    res = test_db.post("/api/v1/cache/invalidate", json={}, headers=headers)
    assert res.status_code == 403
def test_developer_cannot_create_api_key(test_db):
    """4. Developer -> cannot create API key"""
    _, headers = _setup_user(test_db, "dev1@sentinel.ai", role_id="role-developer")
    res = test_db.post("/api/v1/virtual-keys", json={"name": "K1"}, headers=headers)
    assert res.status_code == 403
def test_developer_cannot_invalidate_cache(test_db):
    """5. Developer -> cannot invalidate cache"""
    _, headers = _setup_user(test_db, "dev2@sentinel.ai", role_id="role-developer")
    res = test_db.post("/api/v1/cache/invalidate", json={}, headers=headers)
    assert res.status_code == 403
def test_developer_can_chat(test_db):
    """6. Developer -> can chat"""
    _, headers = _setup_user(test_db, "dev3@sentinel.ai", role_id="role-developer")
    res = test_db.get("/api/v1/conversations", headers=headers)
    assert res.status_code == 200
def test_developer_can_view_models(test_db):
    """7. Developer -> can view models catalog"""
    _, headers = _setup_user(test_db, "dev4@sentinel.ai", role_id="role-developer")
    res = test_db.get("/api/v1/models", headers=headers)
    assert res.status_code == 200
def test_ai_engineer_can_manage_models(test_db):
    """8. AI Engineer -> can manage models / providers"""
    _, headers = _setup_user(test_db, "aieng1@sentinel.ai", role_id="role-ai-engineer")
    res = test_db.post("/api/v1/providers/gemini/toggle?enabled=true", headers=headers)
    assert res.status_code == 200
def test_ai_engineer_can_manage_cache(test_db):
    """9. AI Engineer -> can manage cache"""
    _, headers = _setup_user(test_db, "aieng2@sentinel.ai", role_id="role-ai-engineer")
    res = test_db.post("/api/v1/cache/invalidate", json={"workspace_id": "default"}, headers=headers)
    assert res.status_code == 200
def test_ai_engineer_can_manage_guardrails(test_db):
    """10. AI Engineer -> can manage guardrails / scan"""
    _, headers = _setup_user(test_db, "aieng3@sentinel.ai", role_id="role-ai-engineer")
    res = test_db.post("/api/v1/guardrails/scan", json={"prompt": "Test prompt"}, headers=headers)
    assert res.status_code == 200
def test_ai_engineer_cannot_manage_billing(test_db):
    """11. AI Engineer -> cannot manage billing"""
    _, headers = _setup_user(test_db, "aieng4@sentinel.ai", role_id="role-ai-engineer")
    res = test_db.post("/api/v1/finops/budgets", json={"workspace_id": "default", "monthly_budget_usd": 500}, headers=headers)
    assert res.status_code == 403
def test_ai_engineer_cannot_manage_users(test_db):
    """12. AI Engineer -> cannot manage users / roles"""
    _, headers = _setup_user(test_db, "aieng5@sentinel.ai", role_id="role-ai-engineer")
    res = test_db.post("/api/v1/roles/assign", json={"user_id": "u1", "role_id": "role-super-admin"}, headers=headers)
    assert res.status_code == 403
def test_workspace_admin_can_manage_workspace_api_keys(test_db):
    """13. Workspace Admin -> can manage workspace API keys"""
    _, headers = _setup_user(test_db, "wsadmin@sentinel.ai", role_id="role-workspace-admin")
    res = test_db.post("/api/v1/virtual-keys", json={"name": "WS Key 1"}, headers=headers)
    assert res.status_code == 201
def test_org_admin_can_manage_users_and_billing(test_db):
    """14. Organization Admin -> can manage users / billing"""
    _, headers = _setup_user(test_db, "orgadmin@sentinel.ai", role_id="role-org-admin")
    res1 = test_db.get("/api/v1/roles", headers=headers)
    assert res1.status_code == 200
    res2 = test_db.post("/api/v1/finops/budgets", json={"workspace_id": "default", "monthly_budget_usd": 1000}, headers=headers)
    assert res2.status_code == 200
def test_super_admin_full_access(test_db):
    """15. Super Admin -> full access"""
    _, headers = _setup_user(test_db, settings.bootstrap_admin_email, role_id="role-super-admin")
    res = test_db.get("/api/v1/audit", headers=headers)
    assert res.status_code == 200
def test_cross_workspace_ai_engineer_access_denied(test_db):
    """16. Cross-workspace AI Engineer access -> denied"""
    _, headers = _setup_user(test_db, "aieng_cross@sentinel.ai", role_id="role-ai-engineer")
    res = test_db.post("/api/v1/workspaces", json={"org_id": "unassigned_org", "name": "Hack WS", "slug": "hack-ws"}, headers=headers)
    assert res.status_code == 403
def test_cross_organization_access_denied(test_db):
    """17. Cross-organization access -> denied"""
    _, headers = _setup_user(test_db, "dev_cross@sentinel.ai", role_id="role-developer")
    res = test_db.post("/api/v1/organizations", json={"name": "Unauth Org", "slug": "unauth-org", "domain": "unauth.com"}, headers=headers)
    assert res.status_code == 403
def test_all_roles_model_read_access(test_db):
    """18. Verify Super Admin, Org Admin, Workspace Admin, AI Engineer, Analyst, Developer can view models."""
    roles_to_test = [
        ("super_admin_view@sentinel.ai", "role-super-admin"),
        ("org_admin_view@sentinel.ai", "role-org-admin"),
        ("ws_admin_view@sentinel.ai", "role-workspace-admin"),
        ("ai_eng_view@sentinel.ai", "role-ai-engineer"),
        ("analyst_view@sentinel.ai", "role-analyst"),
        ("dev_view@sentinel.ai", "role-developer"),
    ]
    for email, role_id in roles_to_test:
        _, headers = _setup_user(test_db, email, role_id=role_id)
        res = test_db.get("/api/v1/models", headers=headers)
        assert res.status_code == 200, f"Failed for {role_id}: {res.status_code}"
def test_developer_cannot_manage_models_or_providers_or_users(test_db):
    """19. Verify Developer cannot manage models, providers, or users."""
    _, headers = _setup_user(test_db, "dev_restrictions@sentinel.ai", role_id="role-developer")
    # Developer cannot manage providers/models
    res1 = test_db.post("/api/v1/providers/gemini/toggle?enabled=true", headers=headers)
    assert res1.status_code == 403
    # Developer cannot manage users
    res2 = test_db.post("/api/v1/roles/assign", json={"user_id": "u1", "role_id": "role-developer"}, headers=headers)
    assert res2.status_code == 403
def test_unauthorized_custom_role_cannot_view_models(test_db):
    """20. Custom role without view_models receives 403 on GET /api/v1/models."""
    custom_role = role_repository.create_role(
        name="Restricted Role",
        description="Role without view_models",
        permissions=["chat.read"],
    )
    _, headers = _setup_user(test_db, "restricted@sentinel.ai", role_id=custom_role.id)
    res = test_db.get("/api/v1/models", headers=headers)
    assert res.status_code == 403
    assert "Permission denied" in res.json()["detail"]
