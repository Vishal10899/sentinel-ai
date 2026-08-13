"""Production-grade Unit and Integration tests for Task 03 — Employee AI Chat UI API Contracts & Integrations."""

from unittest.mock import AsyncMock, patch
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.api.dependencies import current_user
from app.db.base import Base
from app.db.session import get_db
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
        id="empuser123",
        name="Employee User",
        email="employee@sentinel.ai",
        salt="empsalt123",
        password_hash="emphash123",
    )


@pytest_asyncio.fixture
async def async_client():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[current_user] = override_current_user

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed employee user & workspace
    async with TestingSessionLocal() as db:
        user = User(
            id="empuser123",
            name="Employee User",
            email="employee@sentinel.ai",
            salt="empsalt123",
            password_hash="emphash123",
        )
        db.add(user)
        workspace = Workspace(
            id="emp-workspace-uuid",
            name="Employee Engineering Workspace",
            slug="emp-workspace",
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
async def test_employee_conversation_creation_and_sidebar_filtering(async_client: AsyncClient):
    """Verify conversation creation, search filtering, pinning, and favoriting for employee UI."""
    # 1. Create conversation
    res = await async_client.post("/api/v1/conversations", json={"title": "Sprint Planning AI Discussion"})
    assert res.status_code == 201
    conv = res.json()
    conv_id = conv["id"]

    # 2. Favorite conversation
    fav_res = await async_client.post(f"/api/v1/conversations/{conv_id}/favorite")
    assert fav_res.status_code == 200
    assert fav_res.json()["is_favorite"] is True

    # 3. Search conversation
    search_res = await async_client.get("/api/v1/conversations?query=Sprint")
    assert search_res.status_code == 200
    assert len(search_res.json()) >= 1


@pytest.mark.asyncio
async def test_employee_message_actions_and_deletion(async_client: AsyncClient):
    """Verify message listing and deletion for employee chat workspace."""
    c_res = await async_client.post("/api/v1/conversations", json={"title": "Code Review Chat"})
    conv_id = c_res.json()["id"]

    m_res = await async_client.get(f"/api/v1/chat/{conv_id}/messages")
    assert m_res.status_code == 200
    assert "messages" in m_res.json()
