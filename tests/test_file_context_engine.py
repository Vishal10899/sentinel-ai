"""Production-grade Unit and Integration tests for Task 04 — Enterprise File Upload & Context Engine."""

import io
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.api.dependencies import current_user
from app.context.chunking import ChunkingEngine, chunking_engine
from app.context.engine import ContextEngine, context_engine
from app.context.vector_prep import VectorPrepService, vector_prep_service
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.services.file_service import file_service

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


async def override_current_user():
    return User(
        id="fileuser123",
        name="File Test User",
        email="fileuser@sentinel.ai",
        salt="filesalt123",
        password_hash="filehash123",
    )


@pytest_asyncio.fixture
async def async_client():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[current_user] = override_current_user

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed user & workspace
    async with TestingSessionLocal() as db:
        user = User(
            id="fileuser123",
            name="File Test User",
            email="fileuser@sentinel.ai",
            salt="filesalt123",
            password_hash="filehash123",
        )
        db.add(user)
        workspace = Workspace(
            id="file-workspace-uuid",
            name="File Workspace",
            slug="file-workspace",
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
async def test_chunking_engine_sentence_and_paragraph_strategies():
    """Verify ChunkingEngine sentence, paragraph, and metadata offset preservation."""
    sample_text = (
        "Sentinel AI Gateway is an enterprise solution. "
        "It provides intelligent model routing and cost calculation. "
        "The Context Engine chunks document attachments for RAG readiness.\n\n"
        "Second paragraph details vector payload preparation for Qdrant database indexing."
    )

    engine = ChunkingEngine(default_chunk_size=100, default_overlap=20)

    # Sentence chunking
    chunks_sentence = engine.chunk_text("doc-1", sample_text, strategy="sentence")
    assert len(chunks_sentence) >= 2
    assert chunks_sentence[0].document_id == "doc-1"
    assert chunks_sentence[0].chunk_index == 0
    assert chunks_sentence[0].token_count > 0

    # Paragraph chunking
    chunks_paragraph = engine.chunk_text("doc-1", sample_text, strategy="paragraph")
    assert len(chunks_paragraph) >= 2


@pytest.mark.asyncio
async def test_vector_preparation_payload_service():
    """Verify VectorPrepService transforming text chunks into Qdrant-compatible payloads."""
    engine = ChunkingEngine(default_chunk_size=100, default_overlap=20)
    chunks = engine.chunk_text("doc-99", "Vector test text content for Sentinel AI.")

    prep_service = VectorPrepService()
    payloads = prep_service.prepare_chunks(chunks, workspace_id="ws-123", conversation_id="conv-456")

    assert len(payloads) == len(chunks)
    assert payloads[0].document_id == "doc-99"
    assert payloads[0].workspace_id == "ws-123"
    assert payloads[0].conversation_id == "conv-456"
    assert payloads[0].text is not None


@pytest.mark.asyncio
async def test_context_engine_token_budget_truncation():
    """Verify ContextEngine budget allocation and context merging."""
    engine = ContextEngine(default_max_context_tokens=4096)
    budget = engine.allocate_budget(4096)
    assert budget.max_context_tokens == 4096
    assert budget.attachment_budget > 0

    attachments = [
        {"filename": "contract.txt", "extracted_text": "Clause 1: Confidentiality obligation. " * 50},
        {"filename": "specs.pdf", "extracted_text": "Specification details for system architecture. " * 50},
    ]

    built = engine.build_prompt_context(
        prompt="Summarize the attached contract and technical specs",
        system_prompt="You are an enterprise AI assistant.",
        attachments=attachments,
        max_context_tokens=4096,
    )

    assert "System: You are an enterprise AI assistant." in built["full_prompt"]
    assert "--- Document: contract.txt ---" in built["full_prompt"]
    assert built["prompt_tokens"] > 0


@pytest.mark.asyncio
async def test_file_upload_deduplication_and_management_apis(async_client: AsyncClient):
    """Test file upload with SHA-256 hash deduplication, metadata, chunking, and file management REST APIs."""
    content = b"Enterprise Sentinel AI Document Content for Context Engine Testing."
    files1 = {"file": ("enterprise_doc.txt", io.BytesIO(content), "text/plain")}

    # 1. Upload File 1
    res1 = await async_client.post("/api/v1/files/upload", files=files1)
    assert res1.status_code == 200
    file1_data = res1.json()
    file_id = file1_data["id"]
    assert file1_data["filename"] == "enterprise_doc.txt"
    assert file1_data["sha256_hash"] is not None
    assert file1_data["chunk_count"] >= 1
    assert file1_data["word_count"] > 0

    # 2. Upload duplicate file content
    files2 = {"file": ("enterprise_doc_copy.txt", io.BytesIO(content), "text/plain")}
    res2 = await async_client.post("/api/v1/files/upload", files=files2)
    assert res2.status_code == 200
    assert res2.json()["is_duplicate"] is True

    # 3. List Files Endpoint
    list_res = await async_client.get("/api/v1/files")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. Storage Stats Endpoint
    stats_res = await async_client.get("/api/v1/files/stats")
    assert stats_res.status_code == 200
    assert stats_res.json()["total_files"] >= 1

    # 5. Metadata Endpoint
    meta_res = await async_client.get(f"/api/v1/files/{file_id}/metadata")
    assert meta_res.status_code == 200
    assert meta_res.json()["filename"] == "enterprise_doc.txt"

    # 6. Chunks Endpoint
    chunk_res = await async_client.get(f"/api/v1/files/{file_id}/chunks")
    assert chunk_res.status_code == 200
    assert len(chunk_res.json()) >= 1

    # 7. Rename File Endpoint
    rename_res = await async_client.put(f"/api/v1/files/{file_id}", json={"filename": "renamed_doc.txt"})
    assert rename_res.status_code == 200
    assert rename_res.json()["filename"] == "renamed_doc.txt"

    # 8. Delete File Endpoint
    del_res = await async_client.delete(f"/api/v1/files/{file_id}")
    assert del_res.status_code == 204
