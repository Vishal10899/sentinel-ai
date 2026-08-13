"""Unit and Integration tests for Phase 1.5 & Phase 1.6 Enterprise AI Playground & Conversation System."""

import io
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
from app.providers.manager import provider_manager

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


async def override_current_user():
    return User(
        id="testuser123",
        name="Test User",
        email="test@sentinel.ai",
        salt="testsalt123",
        password_hash="testhash123",
    )


@pytest_asyncio.fixture
async def async_client():
    from app.core.settings import settings
    from app.providers import provider_manager, register_configured_providers
    from app.rbac import rbac_engine

    rbac_engine.check_permission = lambda *args, **kwargs: True
    provider_manager.clear()
    register_configured_providers(provider_manager, settings)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[current_user] = override_current_user
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed test user & workspace in DB
    async with TestingSessionLocal() as db:
        user = User(
            id="testuser123",
            name="Test User",
            email="test@sentinel.ai",
            salt="testsalt123",
            password_hash="testhash123",
        )
        db.add(user)
        workspace = Workspace(
            id="test-workspace-uuid",
            name="Test Workspace",
            slug="test-workspace",
            owner_id=user.id,
        )
        db.add(workspace)
        await db.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    await test_engine.dispose()


@pytest.mark.asyncio
async def test_create_and_manage_conversation(async_client: AsyncClient):
    """Test Conversation CRUD, search, pin, archive, and export."""
    # 1. Create Conversation
    res = await async_client.post(
        "/api/v1/conversations",
        json={"title": "Test AI Architecture Conversation"},
    )
    assert res.status_code == 201
    conv = res.json()
    conv_id = conv["id"]
    assert conv["title"] == "Test AI Architecture Conversation"
    assert conv["is_pinned"] is False
    assert conv["is_archived"] is False

    # 2. List Conversations
    res_list = await async_client.get("/api/v1/conversations")
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) >= 1

    # 3. Search Conversations
    res_search = await async_client.get("/api/v1/conversations?query=Architecture")
    assert res_search.status_code == 200
    assert len(res_search.json()) >= 1

    # 4. Toggle Pin
    res_pin = await async_client.post(f"/api/v1/conversations/{conv_id}/pin")
    assert res_pin.status_code == 200
    assert res_pin.json()["is_pinned"] is True

    # 5. Toggle Archive
    res_archive = await async_client.post(f"/api/v1/conversations/{conv_id}/archive")
    assert res_archive.status_code == 200
    assert res_archive.json()["is_archived"] is True

    # 6. Export Conversation
    res_export = await async_client.get(f"/api/v1/conversations/{conv_id}/export")
    assert res_export.status_code == 200
    exp = res_export.json()
    assert exp["conversation"]["id"] == conv_id

    # 7. Soft Delete Conversation
    res_del = await async_client.delete(f"/api/v1/conversations/{conv_id}")
    assert res_del.status_code == 204


@pytest.mark.asyncio
async def test_conversation_duplication_favorite_soft_delete_and_sharing(async_client: AsyncClient):
    """Test Conversation duplication, favorite, restore, permanent delete, share link, and public viewing."""
    # 1. Create conversation
    c_res = await async_client.post("/api/v1/conversations", json={"title": "Original Conversation"})
    conv_id = c_res.json()["id"]

    # 2. Toggle Favorite
    fav_res = await async_client.post(f"/api/v1/conversations/{conv_id}/favorite")
    assert fav_res.status_code == 200
    assert fav_res.json()["is_favorite"] is True

    # 3. Duplicate Conversation
    dup_res = await async_client.post(f"/api/v1/conversations/{conv_id}/duplicate")
    assert dup_res.status_code == 200
    dup_data = dup_res.json()
    assert "Copy of Original Conversation" in dup_data["title"]

    # 4. Generate Share Link
    share_res = await async_client.post(f"/api/v1/conversations/{conv_id}/share")
    assert share_res.status_code == 200
    token = share_res.json()["share_token"]

    # 5. Public View Shared Conversation
    public_res = await async_client.get(f"/api/v1/conversations/shared/{token}")
    assert public_res.status_code == 200
    assert public_res.json()["title"] == "Original Conversation"

    # 6. Soft Delete and Restore
    del_res = await async_client.delete(f"/api/v1/conversations/{conv_id}")
    assert del_res.status_code == 204

    restore_res = await async_client.post(f"/api/v1/conversations/{conv_id}/restore")
    assert restore_res.status_code == 200
    assert restore_res.json()["is_deleted"] is False

    # 7. Permanent Delete
    perm_res = await async_client.delete(f"/api/v1/conversations/{conv_id}/permanent")
    assert perm_res.status_code == 204


@pytest.mark.asyncio
async def test_file_upload_attachment(async_client: AsyncClient):
    """Test file upload validation and text extraction for attachments."""
    txt_content = b"Sentinel AI Gateway Enterprise Architecture File Test Content"
    files = {"file": ("test_file.txt", io.BytesIO(txt_content), "text/plain")}

    res = await async_client.post("/api/v1/files/upload", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["filename"] == "test_file.txt"
    assert "Sentinel AI Gateway" in data["extracted_text"]
    assert data["size_bytes"] == len(txt_content)


@pytest.mark.asyncio
async def test_file_magic_bytes_validation(async_client: AsyncClient):
    """Test virus-safe binary magic bytes signature validation."""
    # Valid PDF magic header %PDF-
    pdf_content = b"%PDF-1.4 valid test pdf binary content"
    res_pdf = await async_client.post(
        "/api/v1/files/upload",
        files={"file": ("doc.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    assert res_pdf.status_code == 200

    # Invalid PDF content disguised with .pdf extension
    invalid_pdf = b"malicious binary disguised as pdf"
    res_invalid = await async_client.post(
        "/api/v1/files/upload",
        files={"file": ("fake.pdf", io.BytesIO(invalid_pdf), "application/pdf")},
    )
    assert res_invalid.status_code == 400
    assert "Invalid PDF file header" in res_invalid.json()["detail"]


@pytest.mark.asyncio
async def test_playground_chat_generation(async_client: AsyncClient):
    """Test unified chat completion with auto-routing and parameter support."""
    # 1. Create conversation
    res_conv = await async_client.post(
        "/api/v1/conversations",
        json={"title": "Chat Test Conversation"},
    )
    assert res_conv.status_code == 201
    conv_id = res_conv.json()["id"]

    # Mock provider generation response
    mock_provider = AsyncMock()
    mock_provider.name = "mock_provider"
    mock_provider.generate.return_value = "Mock LLM completion response for Sentinel AI Gateway."

    with patch.object(provider_manager, "get", return_value=mock_provider):
        chat_payload = {
            "conversation_id": conv_id,
            "prompt": "What is the optimal latency strategy for AI gateway routing?",
            "strategy": "fastest",
            "system_prompt": "You are Sentinel AI assistant.",
            "temperature": 0.7,
            "top_p": 1.0,
            "max_tokens": 512,
        }

        res_chat = await async_client.post("/api/v1/chat", json=chat_payload)
        assert res_chat.status_code == 200
        chat_resp = res_chat.json()
        assert chat_resp["conversation_id"] == conv_id
        assert chat_resp["provider"] is not None
        assert chat_resp["model"] is not None
        assert chat_resp["prompt_tokens"] > 0
        assert chat_resp["completion_tokens"] > 0
        assert chat_resp["total_tokens"] > 0

    # Retrieve conversation messages
    res_msgs = await async_client.get(f"/api/v1/chat/{conv_id}/messages")
    assert res_msgs.status_code == 200
    msgs = res_msgs.json()["messages"]
    assert len(msgs) == 2  # user + assistant
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_chat_sse_streaming(async_client: AsyncClient):
    """Test SSE streaming endpoint yielding token events."""
    mock_provider = AsyncMock()
    mock_provider.name = "mock_provider"
    mock_provider.generate.return_value = "Mock LLM token streaming response."

    with patch.object(provider_manager, "get", return_value=mock_provider):
        chat_payload = {
            "prompt": "Explain streaming LLM token delivery via Server-Sent Events.",
            "strategy": "balanced",
        }

        res_stream = await async_client.post("/api/v1/chat/stream", json=chat_payload)
        assert res_stream.status_code == 200
        assert "text/event-stream" in res_stream.headers["content-type"]
        body = res_stream.text
        assert "event: metadata" in body
        assert "event: token" in body
        assert "event: done" in body
