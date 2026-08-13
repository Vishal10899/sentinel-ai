"""Enterprise File Management & Context Inspection API Router."""

import os
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.api.dependencies import current_user
from app.models.user import User
from app.services.file_service import file_service

router = APIRouter(prefix="/files", tags=["files"])


class RenameFileRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)


@router.post("/upload", summary="Upload attachment with deduplication and chunking")
async def upload_file(file: UploadFile = File(...), user: User = Depends(current_user)):
    """Upload PDF, DOCX, TXT, MD, CSV, JSON, XML, HTML, Image, or Office attachment."""
    return await file_service.process_upload(file)


@router.get("", summary="List uploaded files")
async def list_files(query: str | None = Query(default=None), user: User = Depends(current_user)):
    """List uploaded files with optional search query filtering."""
    return file_service.list_files(query=query)


@router.get("/stats", summary="Get storage and parsing statistics")
async def get_storage_stats(user: User = Depends(current_user)):
    """Retrieve overall storage telemetry, format breakdowns, and chunk counts."""
    return file_service.get_stats()


@router.get("/{file_id}/metadata", summary="Get document metadata and parsing details")
async def get_file_metadata(file_id: str, user: User = Depends(current_user)):
    """Inspect detailed document metadata (page count, word count, character count, token estimate, SHA-256 hash)."""
    meta = file_service.get_metadata(file_id)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File metadata not found")
    return meta


@router.get("/{file_id}/chunks", summary="Get document text chunks")
async def get_file_chunks(file_id: str, user: User = Depends(current_user)):
    """Retrieve text chunks generated for vector database ingestion."""
    return file_service.get_chunks(file_id)


@router.put("/{file_id}", summary="Rename uploaded file")
async def rename_file(file_id: str, request: RenameFileRequest, user: User = Depends(current_user)):
    """Rename an uploaded document record."""
    renamed = file_service.rename_file(file_id, request.filename)
    if not renamed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return renamed


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete uploaded file")
async def delete_file(file_id: str, user: User = Depends(current_user)):
    """Delete an uploaded file record and clear associated disk storage."""
    deleted = file_service.delete_file(file_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")


@router.get("/{filename}", summary="Download / preview uploaded file")
async def get_uploaded_file(filename: str, user: User = Depends(current_user)):
    """Retrieve raw uploaded attachment file."""
    file_path = os.path.join(file_service.upload_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(file_path)
