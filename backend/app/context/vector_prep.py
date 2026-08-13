import json
from dataclasses import asdict, dataclass
from typing import Any
from uuid import uuid4

from app.context.chunking import Chunk


@dataclass
class VectorPayload:
    """Standardized metadata payload prepared for Qdrant or external vector store indexing."""

    vector_id: str
    document_id: str
    workspace_id: str
    conversation_id: str | None
    chunk_id: str
    chunk_index: int
    start_char: int
    end_char: int
    token_count: int
    text: str
    metadata_json: str

    def to_qdrant_payload() -> dict[str, Any]:
        """Convert into Qdrant point payload dictionary."""
        return {
            "id": self.vector_id,
            "payload": {
                "document_id": self.document_id,
                "workspace_id": self.workspace_id,
                "conversation_id": self.conversation_id,
                "chunk_id": self.chunk_id,
                "chunk_index": self.chunk_index,
                "start_char": self.start_char,
                "end_char": self.end_char,
                "token_count": self.token_count,
                "text": self.text,
                "metadata": json.loads(self.metadata_json) if self.metadata_json else {},
            },
        }


class VectorPrepService:
    """Prepares document chunks and attachments for vector database embedding insertion."""

    def prepare_chunks(
        self,
        chunks: list[Chunk],
        workspace_id: str,
        conversation_id: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> list[VectorPayload]:
        """Transform text chunks into vector store payload records."""
        payloads: list[VectorPayload] = []
        meta = extra_metadata or {}

        for chunk in chunks:
            vector_id = str(uuid4())
            payloads.append(
                VectorPayload(
                    vector_id=vector_id,
                    document_id=chunk.document_id,
                    workspace_id=workspace_id,
                    conversation_id=conversation_id,
                    chunk_id=chunk.chunk_id,
                    chunk_index=chunk.chunk_index,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                    token_count=chunk.token_count,
                    text=chunk.text,
                    metadata_json=json.dumps(meta),
                )
            )

        return payloads


vector_prep_service = VectorPrepService()
