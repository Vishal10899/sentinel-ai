import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.base import Base
from app.db.session import get_db


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


def test_register_and_workspace_creation(test_db):
    """Verify registration, password hashing, DB insert, workspace creation, and JWT output."""
    register_payload = {
        "name": "Sentinel Admin",
        "email": "admin@sentinel.ai",
        "password": "SecurePassword123!"
    }
    response = test_db.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 200, f"Register failed: {response.text}"
    
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@sentinel.ai"
    assert data["user"]["name"] == "Sentinel Admin"

    # Verify JWT validity
    token = data["access_token"]
    user_info = test_db.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert user_info.status_code == 200
    me_json = user_info.json()
    assert (me_json.get("email") or me_json.get("user", {}).get("email")) == "admin@sentinel.ai"


def test_duplicate_user_handling(test_db):
    """Verify duplicate registration fails with 409 Conflict."""
    payload = {
        "name": "Sentinel Admin",
        "email": "duplicate@sentinel.ai",
        "password": "SecurePassword123!"
    }
    res1 = test_db.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 200

    res2 = test_db.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert res2.json()["detail"] == "An account already exists for this email"


def test_login_and_password_hashing(test_db):
    """Verify login with correct and incorrect passwords."""
    payload = {
        "name": "Login User",
        "email": "user@sentinel.ai",
        "password": "MySecretPassword123!"
    }
    reg_res = test_db.post("/api/v1/auth/register", json=payload)
    assert reg_res.status_code == 200

    # Successful login
    login_res = test_db.post("/api/v1/auth/login", json={
        "email": "user@sentinel.ai",
        "password": "MySecretPassword123!"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Wrong password login
    bad_login = test_db.post("/api/v1/auth/login", json={
        "email": "user@sentinel.ai",
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401


def test_ai_workspace_authentication(test_db):
    """Verify user registration automatically creates an AI Workspace for the user."""
    payload = {
        "name": "AI Engineer",
        "email": "ai.engineer@sentinel.ai",
        "password": "SecurePassword123!"
    }
    res = test_db.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 200
    token = res.json()["access_token"]

    # Verify protected endpoint access with JWT
    me_res = test_db.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_json = me_res.json()
    uid = me_json.get("user_id") or me_json.get("user", {}).get("user_id")
    assert uid == res.json()["user"]["user_id"]
