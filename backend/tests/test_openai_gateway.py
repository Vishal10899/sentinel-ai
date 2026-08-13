import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.core.settings import settings
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.providers import provider_manager, register_configured_providers
from app.security.keys import VirtualKeyType
from app.security.repository import virtual_key_repository


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
def test_client():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with session_factory() as db:
            user = User(id="system_user", name="System User", email="system@sentinel.ai", salt="s", password_hash="h")
            ws = Workspace(id="default", name="Default Workspace", slug="default", owner_id=user.id, is_active=True)
            db.add(user)
            db.add(ws)
            await db.commit()

    asyncio.run(init_db())

    async def _get_test_db():
        async with session_factory() as session:
            yield session

    register_configured_providers(provider_manager, settings)
    provider_manager.configure("gemini", enabled=True, api_key="dummy_gemini_key", status="healthy")
    provider_manager.configure("ollama", enabled=True, base_url="http://localhost:11434", status="healthy")

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


def test_1_valid_api_key_creation_and_auth(test_client):
    """Test 1: Valid Virtual API Key authentication."""
    raw_secret, key_obj = virtual_key_repository.create_key(
        workspace_id="default",
        name="Test Gateway Key 1",
        key_type=VirtualKeyType.WORKSPACE,
    )
    assert raw_secret.startswith("sk-snt-live-")

    headers = {"Authorization": f"Bearer {raw_secret}"}
    res = test_client.get("/v1/models", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["object"] == "list"
    assert len(data["data"]) > 0


def test_2_invalid_api_key(test_client):
    """Test 2: Invalid Virtual API Key returns 401 Unauthorized."""
    headers = {"Authorization": "Bearer sk-snt-live-invalidkey1234567890"}
    res = test_client.get("/v1/models", headers=headers)
    assert res.status_code == 401


def test_3_disabled_key(test_client):
    """Test 3: Disabled/Revoked Virtual Key returns 401 Unauthorized."""
    raw_secret, key_obj = virtual_key_repository.create_key(
        workspace_id="default",
        name="Test Revoked Key",
    )
    virtual_key_repository.revoke_key(key_obj.id)

    headers = {"Authorization": f"Bearer {raw_secret}"}
    res = test_client.get("/v1/models", headers=headers)
    assert res.status_code == 401


def test_4_unauthorized_workspace_permissions(test_client):
    """Test 4: Virtual Key restricted to specific provider blocks unauthorized providers."""
    raw_secret, key_obj = virtual_key_repository.create_key(
        workspace_id="default",
        name="Restricted Key",
        allowed_providers=["ollama"],  # Only Ollama allowed
    )

    headers = {"Authorization": f"Bearer {raw_secret}"}
    payload = {
        "model": "gemini/gemini-2.0-flash",
        "messages": [{"role": "user", "content": "Hello"}],
    }
    res = test_client.post("/v1/chat/completions", headers=headers, json=payload)
    assert res.status_code == 403


def test_5_non_streaming_request(test_client):
    """Test 5: Non-streaming POST /v1/chat/completions returning OpenAI JSON response."""
    raw_secret, key_obj = virtual_key_repository.create_key(
        workspace_id="default",
        name="Test Non Streaming Key",
    )

    mock_gemini = AsyncMock()
    mock_gemini.name = "gemini"
    async def mock_generate(prompt, **kwargs):
        return "Quantum mechanics is the branch of physics studying subatomic particles."
    mock_gemini.generate = mock_generate

    headers = {"Authorization": f"Bearer {raw_secret}"}
    payload = {
        "model": "gemini-2.0-flash",
        "messages": [
            {"role": "system", "content": "You are a physics expert."},
            {"role": "user", "content": "Explain quantum mechanics in one sentence."},
        ],
        "stream": False,
        "temperature": 0.5,
    }

    with patch.object(provider_manager, "get", return_value=mock_gemini):
        res = test_client.post("/v1/chat/completions", headers=headers, json=payload)
        assert res.status_code == 200, f"Failed: {res.text}"
        data = res.json()
        assert data["object"] == "chat.completion"
        assert len(data["choices"]) > 0
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert "Quantum mechanics" in data["choices"][0]["message"]["content"]
        assert "usage" in data
        assert "sentinel_telemetry" in data


def test_6_streaming_request(test_client):
    """Test 6: Streaming POST /v1/chat/completions returning OpenAI SSE data chunks."""
    raw_secret, key_obj = virtual_key_repository.create_key(
        workspace_id="default",
        name="Test Streaming Key",
    )

    mock_ollama = AsyncMock()
    mock_ollama.name = "ollama"
    async def mock_stream_gen(prompt, **kwargs):
        yield "Hello! "
        yield "This is a stream."
    mock_ollama.stream_generate = mock_stream_gen

    headers = {"Authorization": f"Bearer {raw_secret}"}
    payload = {
        "model": "ollama/llama3.2",
        "messages": [{"role": "user", "content": "Stream test"}],
        "stream": True,
    }

    with patch.object(provider_manager, "get", return_value=mock_ollama):
        res = test_client.post("/v1/chat/completions", headers=headers, json=payload)
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        body_text = res.text
        assert "data: {" in body_text
        assert "chat.completion.chunk" in body_text
        assert "data: [DONE]" in body_text


def test_7_routing_auto_strategy(test_client):
    """Test 7: Model 'auto' routes through AdaptiveRouter dynamically."""
    raw_secret, key_obj = virtual_key_repository.create_key(
        workspace_id="default",
        name="Routing Key",
    )

    headers = {"Authorization": f"Bearer {raw_secret}"}
    payload = {
        "model": "auto",
        "messages": [{"role": "user", "content": "Write Python code for quicksort"}],
        "stream": False,
    }

    mock_prov = AsyncMock()
    mock_prov.name = "ollama"
    async def mock_gen(prompt, **kwargs):
        return "def quicksort(arr): return arr"
    mock_prov.generate = mock_gen

    with patch.object(provider_manager, "get", return_value=mock_prov):
        res = test_client.post("/v1/chat/completions", headers=headers, json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "choices" in data


def test_8_gemini_execution(test_client):
    """Test 8: Real/mock Gemini execution through gateway."""
    raw_secret, key_obj = virtual_key_repository.create_key(workspace_id="default", name="Gemini Test Key")
    headers = {"Authorization": f"Bearer {raw_secret}"}
    payload = {"model": "gemini-2.0-flash", "messages": [{"role": "user", "content": "Hi"}], "stream": False}

    mock_gemini = AsyncMock()
    mock_gemini.name = "gemini"
    async def mock_g(prompt, **kwargs):
        return "Gemini response text"
    mock_gemini.generate = mock_g

    with patch.object(provider_manager, "get", return_value=mock_gemini):
        res = test_client.post("/v1/chat/completions", headers=headers, json=payload)
        assert res.status_code == 200
        assert "Gemini response text" in res.json()["choices"][0]["message"]["content"]


def test_9_ollama_execution(test_client):
    """Test 9: Real/mock Ollama execution through gateway."""
    raw_secret, key_obj = virtual_key_repository.create_key(workspace_id="default", name="Ollama Test Key")
    headers = {"Authorization": f"Bearer {raw_secret}"}
    payload = {"model": "ollama/llama3.2", "messages": [{"role": "user", "content": "Hi"}], "stream": False}

    provider_manager.configure("ollama", enabled=True, base_url="http://127.0.0.1:11434", status="healthy")

    mock_ollama = AsyncMock()
    mock_ollama.name = "ollama"
    mock_ollama.generate = AsyncMock(return_value="Ollama local response text")

    with patch.object(provider_manager, "get", return_value=mock_ollama), patch.object(provider_manager, "is_active", return_value=True):
        res = test_client.post("/v1/chat/completions", headers=headers, json=payload)
        assert res.status_code == 200, f"Failed: {res.text}"
        assert "Ollama local response text" in res.json()["choices"][0]["message"]["content"]




def test_10_gemini_failure_to_ollama_fallback(test_client):
    """Test 10: Gemini 429 failure automatically fails over to Ollama."""
    raw_secret, key_obj = virtual_key_repository.create_key(workspace_id="default", name="Failover Key 1")
    headers = {"Authorization": f"Bearer {raw_secret}"}
    payload = {"model": "gemini/gemini-2.0-flash", "messages": [{"role": "user", "content": "Hi"}], "stream": True}

    provider_manager.configure("gemini", enabled=True, api_key="dummy_gemini_key", status="healthy")
    provider_manager.configure("ollama", enabled=True, base_url="http://localhost:11434", status="healthy")

    mock_failing_gemini = AsyncMock()
    mock_failing_gemini.name = "gemini"
    async def gemini_fail(prompt, **kwargs):
        raise RuntimeError("429 Quota Exceeded")
        yield ""
    mock_failing_gemini.stream_generate = gemini_fail

    mock_working_ollama = AsyncMock()
    mock_working_ollama.name = "ollama"
    async def ollama_ok(prompt, **kwargs):
        yield "Ollama fallback chunk"
    mock_working_ollama.stream_generate = ollama_ok

    def mock_get(p_name):
        if p_name == "gemini":
            return mock_failing_gemini
        if p_name == "ollama":
            return mock_working_ollama
        return provider_manager._providers[p_name]

    with patch.object(provider_manager, "get", side_effect=mock_get):
        res = test_client.post("/v1/chat/completions", headers=headers, json=payload)
        assert res.status_code == 200
        assert "Ollama fallback chunk" in res.text


def test_11_ollama_failure_to_gemini_fallback(test_client):
    """Test 11: Ollama failure automatically fails over to Gemini."""
    raw_secret, key_obj = virtual_key_repository.create_key(workspace_id="default", name="Failover Key 2")
    headers = {"Authorization": f"Bearer {raw_secret}"}
    payload = {"model": "ollama/llama3.2", "messages": [{"role": "user", "content": "Hi"}], "stream": True}

    provider_manager.configure("gemini", enabled=True, api_key="dummy_gemini_key", status="healthy")
    provider_manager.configure("ollama", enabled=True, base_url="http://localhost:11434", status="healthy")

    mock_failing_ollama = AsyncMock()
    mock_failing_ollama.name = "ollama"
    async def ollama_fail(prompt, **kwargs):
        raise RuntimeError("Connection Refused")
        yield ""
    mock_failing_ollama.stream_generate = ollama_fail

    mock_working_gemini = AsyncMock()
    mock_working_gemini.name = "gemini"
    async def gemini_ok(prompt, **kwargs):
        yield "Gemini fallback chunk"
    mock_working_gemini.stream_generate = gemini_ok

    def mock_get(p_name):
        if p_name == "ollama":
            return mock_failing_ollama
        if p_name == "gemini":
            return mock_working_gemini
        return provider_manager._providers[p_name]

    with patch.object(provider_manager, "get", side_effect=mock_get):
        res = test_client.post("/v1/chat/completions", headers=headers, json=payload)
        assert res.status_code == 200
        assert "Gemini fallback chunk" in res.text



def test_12_malformed_request(test_client):
    """Test 12: Missing 'messages' field returns 422 Unprocessable Entity."""
    raw_secret, key_obj = virtual_key_repository.create_key(workspace_id="default", name="Malformed Test Key")
    headers = {"Authorization": f"Bearer {raw_secret}"}
    payload = {"model": "gpt-4o"}
    res = test_client.post("/v1/chat/completions", headers=headers, json=payload)
    assert res.status_code in (400, 422)


def test_13_provider_timeout_and_embeddings(test_client):
    """Test 13: Embeddings endpoint /v1/embeddings."""
    raw_secret, key_obj = virtual_key_repository.create_key(workspace_id="default", name="Embedding Test Key")
    headers = {"Authorization": f"Bearer {raw_secret}"}

    mock_prov = AsyncMock()
    mock_prov.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])

    with patch.object(provider_manager, "get", return_value=mock_prov):
        res = test_client.post("/v1/embeddings", headers=headers, json={"input": "Test embedding text", "model": "text-embedding-004"})
        assert res.status_code == 200
        data = res.json()
        assert data["object"] == "list"
        assert len(data["data"][0]["embedding"]) == 3
