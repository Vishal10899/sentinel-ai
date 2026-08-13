"""Enterprise File Processing & Context Engine Service supporting multi-format document parsing, deduplication, metadata extraction, and chunking."""

import hashlib
import io
import json
import os
import re
import uuid
from datetime import datetime
from typing import Any
from fastapi import HTTPException, UploadFile, status

from app.context.chunking import chunking_engine

ALLOWED_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".xml", ".html", ".pdf", ".docx",
    ".xlsx", ".pptx", ".zip", ".eml", ".png", ".jpg", ".jpeg", ".webp"
}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


class FileService:
    """Validate attachments, compute SHA-256 hashes, extract clean text & metadata, run chunking, and maintain file registry."""

    def __init__(self, upload_dir: str = "uploads") -> None:
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
        self._file_registry: dict[str, dict[str, Any]] = {}
        self._chunk_registry: dict[str, list[dict[str, Any]]] = {}
        self._hash_registry: dict[str, str] = {}  # sha256_hash -> file_id

    async def process_upload(self, file: UploadFile, workspace_id: str = "default") -> dict[str, Any]:
        """Validate, store, hash, extract text & metadata, run chunking on attachment."""
        if not file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename missing")

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

        content = await file.read()
        size = len(content)
        if size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of 20MB (received {size} bytes)",
            )

        # Virus-safe binary magic bytes signature validation
        self._validate_magic_bytes(ext, content)

        # SHA-256 Hash Deduplication
        sha256_hash = hashlib.sha256(content).hexdigest()
        is_duplicate = sha256_hash in self._hash_registry

        file_id = str(uuid.uuid4())
        saved_filename = f"{file_id}{ext}"
        saved_path = os.path.join(self.upload_dir, saved_filename)

        with open(saved_path, "wb") as f:
            f.write(content)

        extracted_text, page_count = self._parse_document_text(ext, content, file.filename)
        word_count = len(re.findall(r"\w+", extracted_text)) if extracted_text else 0
        char_count = len(extracted_text)
        estimated_tokens = max(char_count // 4, 1)

        # Generate text chunks
        chunks = chunking_engine.chunk_text(file_id, extracted_text, page_number=page_count)
        chunk_dicts = [c.to_dict() for c in chunks]

        record = {
            "id": file_id,
            "workspace_id": workspace_id,
            "filename": file.filename,
            "saved_filename": saved_filename,
            "content_type": file.content_type or "application/octet-stream",
            "extension": ext,
            "size_bytes": size,
            "sha256_hash": sha256_hash,
            "is_duplicate": is_duplicate,
            "page_count": page_count,
            "word_count": word_count,
            "character_count": char_count,
            "estimated_tokens": estimated_tokens,
            "chunk_count": len(chunks),
            "extracted_text": extracted_text[:10000],  # Context snippet
            "full_text": extracted_text,
            "status": "processed",
            "created_at": datetime.utcnow().isoformat(),
            "url": f"/files/{saved_filename}",
        }

        self._file_registry[file_id] = record
        self._chunk_registry[file_id] = chunk_dicts
        self._hash_registry[sha256_hash] = file_id

        return record

    def _parse_document_text(self, ext: str, content: bytes, filename: str) -> tuple[str, int]:
        """Extract plain text and page count across document formats."""
        page_count = 1
        extracted_text = ""

        if ext in (".txt", ".md", ".csv", ".json", ".xml", ".html"):
            try:
                extracted_text = content.decode("utf-8", errors="ignore")
                if ext == ".html":
                    extracted_text = re.sub(r"<[^>]+>", " ", extracted_text)
            except Exception:
                extracted_text = ""
        elif ext == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(content))
                page_count = len(reader.pages)
                text_parts = [page.extract_text() or "" for page in reader.pages]
                extracted_text = "\n".join(text_parts)
            except Exception:
                extracted_text = f"[PDF Document attached: {filename}]"
        elif ext == ".docx":
            try:
                import docx
                doc = docx.Document(io.BytesIO(content))
                extracted_text = "\n".join([p.text for p in doc.paragraphs if p.text])
                page_count = max(len(doc.paragraphs) // 30, 1)
            except Exception:
                extracted_text = f"[DOCX Document attached: {filename}]"
        elif ext in (".xlsx", ".pptx", ".zip", ".eml"):
            extracted_text = f"[{ext.upper()[1:]} Container attached: {filename}]"
        elif ext in (".png", ".jpg", ".jpeg", ".webp"):
            extracted_text = f"[Image attached: {filename}]"

        return extracted_text, page_count

    def _validate_magic_bytes(self, ext: str, content: bytes) -> None:
        """Validate binary headers to ensure file extensions match real file signatures."""
        if not content:
            return
        if ext == ".pdf" and not content.startswith(b"%PDF"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PDF file header")
        elif ext == ".png" and not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PNG image header")
        elif ext in (".jpg", ".jpeg") and not content.startswith(b"\xff\xd8\xff"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JPEG image header")
        elif ext in (".docx", ".xlsx", ".pptx", ".zip") and not content.startswith(b"PK\x03\x04"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {ext.upper()} zip package header")

    def list_files(self, workspace_id: str | None = None, query: str | None = None) -> list[dict[str, Any]]:
        """List files in file registry."""
        files = list(self._file_registry.values())
        if workspace_id:
            files = [f for f in files if f["workspace_id"] == workspace_id]
        if query:
            q = query.lower()
            files = [f for f in files if q in f["filename"].lower() or q in f["extension"].lower()]
        return files

    def get_metadata(self, file_id: str) -> dict[str, Any] | None:
        """Retrieve full document metadata."""
        return self._file_registry.get(file_id)

    def get_chunks(self, file_id: str) -> list[dict[str, Any]]:
        """Retrieve chunk records for a file."""
        return self._chunk_registry.get(file_id, [])

    def rename_file(self, file_id: str, new_filename: str) -> dict[str, Any] | None:
        """Rename an existing document record."""
        record = self._file_registry.get(file_id)
        if record:
            record["filename"] = new_filename
        return record

    def delete_file(self, file_id: str) -> bool:
        """Delete file record and associated disk file."""
        record = self._file_registry.get(file_id)
        if not record:
            return False

        saved_path = os.path.join(self.upload_dir, record["saved_filename"])
        if os.path.exists(saved_path):
            try:
                os.remove(saved_path)
            except Exception:
                pass

        if record.get("sha256_hash") in self._hash_registry:
            del self._hash_registry[record["sha256_hash"]]
        del self._file_registry[file_id]
        if file_id in self._chunk_registry:
            del self._chunk_registry[file_id]
        return True

    def get_stats(self, workspace_id: str | None = None) -> dict[str, Any]:
        """Calculate overall storage and file parsing telemetry."""
        files = self.list_files(workspace_id=workspace_id)
        total_files = len(files)
        total_bytes = sum(f["size_bytes"] for f in files)
        total_chunks = sum(f["chunk_count"] for f in files)
        total_words = sum(f["word_count"] for f in files)
        formats = {}
        for f in files:
            ext = f["extension"]
            formats[ext] = formats.get(ext, 0) + 1

        return {
            "total_files": total_files,
            "total_storage_bytes": total_bytes,
            "total_chunks": total_chunks,
            "total_words": total_words,
            "format_breakdown": formats,
        }


file_service = FileService()
