"""Production-grade Unit and Integration tests for Task 02 — Enterprise Streaming AI Gateway."""

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
from app.streaming.manager import stream_manager
from app.streaming.session import StreamSession

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


async def override_current_user():
    return User(
        id="streamuser123",
        name="Stream Test User",
        email="streamuser@sentinel.ai",
        salt="streamsalt123",
        password_hash="streamhash123",
    )


@pytest_asyncio.fixture
async def async_client():
    from app.providers import provider_manager, GeminiProvider, OllamaProvider
    from app.rbac import rbac_engine

    rbac_engine.check_permission = lambda *args, **kwargs: True
    provider_manager.register(GeminiProvider(api_key="sk-test-gemini-key", model="gemini-2.0-flash"))
    provider_manager.register(OllamaProvider(base_url="http://localhost:11434", model="llama3.2"))

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[current_user] = override_current_user
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed user & workspace
    async with TestingSessionLocal() as db:
        user = User(
            id="streamuser123",
            name="Stream Test User",
            email="streamuser@sentinel.ai",
            salt="streamsalt123",
            password_hash="streamhash123",
        )
        db.add(user)
        workspace = Workspace(
            id="stream-workspace-uuid",
            name="Stream Workspace",
            slug="stream-workspace",
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
async def test_stream_session_and_manager_lifecycle():
    """Test StreamSession creation, cancellation, metrics recording, and cleanup."""
    session = stream_manager.create_session(
        conversation_id="conv-123",
        workspace_id="ws-123",
        provider="openai",
        model="gpt-4o",
        routing_strategy="fastest",
    )
    assert session.stream_id in [s["stream_id"] for s in stream_manager.list_active_sessions("ws-123")]

    # Test cancellation
    assert stream_manager.cancel_session(session.stream_id) is True
    assert session.is_cancelled() is True

    # Test metrics
    session.metrics.prompt_tokens = 100
    session.metrics.completion_tokens = 50
    session.metrics.finalize()
    assert session.metrics.total_tokens == 150
    assert session.metrics.total_latency_ms >= 0

    # Cleanup
    stream_manager.cleanup_session(session.stream_id)
    assert stream_manager.get_session(session.stream_id) is None


@pytest.mark.asyncio
async def test_sse_streaming_events_pipeline(async_client: AsyncClient):
    """Test full SSE streaming events pipeline (metadata, routing, token, usage, done)."""
    mock_provider = AsyncMock()
    mock_provider.name = "openai"

    async def mock_stream(prompt, **options):
        tokens = ["Sentinel ", "AI ", "Gateway ", "Enterprise ", "Streaming."]
        for t in tokens:
            yield t

    mock_provider.stream_generate = mock_stream

    with patch.object(provider_manager, "get", return_value=mock_provider):
        chat_payload = {
            "prompt": "Test streaming SSE events pipeline in Sentinel AI",
            "strategy": "balanced",
        }

        res = await async_client.post("/api/v1/chat/stream", json=chat_payload)
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        body = res.text
        assert "event: metadata" in body
        assert "event: routing" in body
        assert "event: token" in body
        assert "event: usage" in body
        assert "event: done" in body


@pytest.mark.asyncio
async def test_stream_cancellation_endpoint(async_client: AsyncClient):
    """Test stream cancellation endpoint POST /chat/stream/{stream_id}/cancel."""
    session = stream_manager.create_session(
        conversation_id="c1",
        workspace_id="stream-workspace-uuid",
        provider="openai",
        model="gpt-4o",
    )

    res = await async_client.post(f"/api/v1/chat/stream/{session.stream_id}/cancel")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert session.is_cancelled() is True

    stream_manager.cleanup_session(session.stream_id)


@pytest.mark.asyncio
async def test_active_streams_listing_endpoint(async_client: AsyncClient):
    """Test active streams listing GET /chat/stream/active."""
    session = stream_manager.create_session(
        conversation_id="c2",
        workspace_id="stream-workspace-uuid",
        provider="gemini",
        model="gemini-1.5-pro",
    )

    res = await async_client.get("/api/v1/chat/stream/active")
    assert res.status_code == 200
    active_list = res.json()
    assert len(active_list) >= 1
    assert active_list[0]["stream_id"] == session.stream_id

    stream_manager.cleanup_session(session.stream_id)


@pytest.mark.asyncio
async def test_stream_failover_mechanism(async_client: AsyncClient):
    """Test automatic failover to fallback provider when primary provider fails."""
    mock_primary = AsyncMock()
    mock_primary.name = "openai"

    async def mock_prim_stream(prompt, **options):
        raise RuntimeError("OpenAI connection timed out")
        yield "Never reached"

    mock_primary.stream_generate = mock_prim_stream

    mock_secondary = AsyncMock()
    mock_secondary.name = "gemini"

    async def mock_sec_stream(prompt, **options):
        yield "Failover response from Gemini"

    mock_secondary.stream_generate = mock_sec_stream

    def mock_get_provider(name):
        if name == "openai":
            return mock_primary
        return mock_secondary

    with patch.object(provider_manager, "is_active", return_value=True), \
         patch.object(provider_manager, "get", side_effect=mock_get_provider):
        chat_payload = {
            "provider": "openai",
            "model": "gpt-4o",
            "prompt": "Failover test request",
        }

        res = await async_client.post("/api/v1/chat/stream", json=chat_payload)
        assert res.status_code == 200
        body = res.text
        assert "Failover response from Gemini" in body
