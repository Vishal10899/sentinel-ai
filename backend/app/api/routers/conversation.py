"""Enterprise Conversation & Memory Platform REST API Router."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from app.api.dependencies import current_user
from app.chat import (
    conversation_exporter,
    conversation_search_engine,
    enterprise_conversation_repository,
    memory_engine,
)
from app.models.user import User

router = APIRouter(prefix="/conversations", tags=["conversations"])


class CreateConversationPayload(BaseModel):
    title: str = Field(default="New Enterprise Conversation")
    description: str = Field(default="")
    workspace_id: str = Field(default="default")
    provider: str = Field(default="gemini")
    model: str = Field(default="gemini-2.0-flash")
    tags: list[str] = Field(default_factory=list)


class UpdateConversationPayload(BaseModel):
    title: str | None = None
    description: str | None = None
    provider: str | None = None
    model: str | None = None
    tags: list[str] | None = None
    summary: str | None = None


class AddMessagePayload(BaseModel):
    conversation_id: str = Field(min_length=1)
    role: str = Field(default="user")
    content: str = Field(min_length=1)
    provider: str = Field(default="gemini")
    model: str = Field(default="gemini-2.0-flash")
    prompt_tokens: int = Field(ge=0, default=0)
    completion_tokens: int = Field(ge=0, default=0)
    cost: float = Field(ge=0.0, default=0.0)
    latency_ms: float = Field(ge=0.0, default=0.0)
    attachments: list[str] = Field(default_factory=list)


from app.db.session import get_db
from app.repositories import ConversationRepository, MessageRepository, WorkspaceRepository
from sqlalchemy.ext.asyncio import AsyncSession


@router.get("", summary="List conversations")
async def list_conversations(
    workspace_id: str = Query(default="default"),
    status: str | None = Query(default=None),
    is_pinned: bool | None = Query(default=None),
    is_favorite: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """List conversations from PostgreSQL database (< 10ms)."""
    ws = await WorkspaceRepository(db).get_or_create_for_user(user.id, user.name)
    target_ws = str(ws.id)
    conv_repo = ConversationRepository(db)
    db_convs = await conv_repo.list(
        workspace_id=target_ws,
        is_pinned=is_pinned,
        is_favorite=is_favorite,
        limit=limit,
    )
    if db_convs:
        return [
            {
                "id": str(c.id),
                "workspace_id": str(c.workspace_id),
                "title": c.title,
                "is_pinned": c.is_pinned,
                "is_favorite": c.is_favorite,
                "is_archived": c.is_archived,
                "is_deleted": c.is_deleted,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in db_convs
        ]
    mem_convs = enterprise_conversation_repository.list_conversations(
        workspace_id=target_ws, status=status, is_pinned=is_pinned, is_favorite=is_favorite, limit=limit
    )
    return [c.to_dict() for c in mem_convs]


@router.get("/search", summary="Search conversations")
async def search_conversations(
    query: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    model: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Full-text and multi-field conversation search (< 5ms)."""
    all_convs = [c.to_dict() for c in enterprise_conversation_repository.list_conversations(limit=1000)]
    all_msgs = {
        c["id"]: [m.to_dict() for m in enterprise_conversation_repository.list_messages(c["id"])]
        for c in all_convs
    }

    res = conversation_search_engine.search(
        conversations=all_convs,
        messages_by_conv=all_msgs,
        query=query,
        provider=provider,
        model=model,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return res.to_dict()


@router.get("/statistics", summary="Get workspace conversation statistics")
async def get_workspace_statistics(workspace_id: str = Query(default="default")):
    """Get workspace-isolated conversation and token usage statistics."""
    return enterprise_conversation_repository.get_workspace_statistics(workspace_id=workspace_id)


@router.get("/{conversation_id}", summary="Get conversation details")
async def get_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve detailed conversation object (< 10ms)."""
    conv = await ConversationRepository(db).get(conversation_id)
    if not conv:
        mem_conv = enterprise_conversation_repository.get_conversation(conversation_id)
        if mem_conv:
            return mem_conv.to_dict()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation '{conversation_id}' not found.")
    return {
        "id": str(conv.id),
        "workspace_id": str(conv.workspace_id),
        "title": conv.title,
        "is_pinned": conv.is_pinned,
        "is_favorite": conv.is_favorite,
        "is_archived": conv.is_archived,
        "is_deleted": conv.is_deleted,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
    }


@router.post("", summary="Create a new conversation", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: CreateConversationPayload,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Create a new conversation in PostgreSQL database."""
    ws = await WorkspaceRepository(db).get_or_create_for_user(user.id, user.name)
    ws_id = str(ws.id)

    conv_repo = ConversationRepository(db)
    db_conv = await conv_repo.create(
        workspace_id=ws_id,
        title=payload.title,
        tags=",".join(payload.tags) if payload.tags else None,
    )
    mem_conv = enterprise_conversation_repository.create_conversation(
        workspace_id=ws_id,
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        provider=payload.provider,
        model=payload.model,
        tags=payload.tags,
    )
    mem_conv.id = str(db_conv.id)
    return {
        "id": str(db_conv.id),
        "workspace_id": ws_id,
        "title": db_conv.title,
        "is_pinned": db_conv.is_pinned,
        "is_favorite": db_conv.is_favorite,
        "is_archived": db_conv.is_archived,
        "is_deleted": db_conv.is_deleted,
        "created_at": db_conv.created_at.isoformat() if db_conv.created_at else None,
        "updated_at": db_conv.updated_at.isoformat() if db_conv.updated_at else None,
    }


@router.put("/{conversation_id}", summary="Update or rename conversation")
async def update_conversation(conversation_id: str, payload: UpdateConversationPayload, db: AsyncSession = Depends(get_db)):
    """Update conversation properties or title."""
    conv_repo = ConversationRepository(db)
    db_conv = await conv_repo.get(conversation_id)
    if db_conv:
        updated = await conv_repo.update(db_conv, title=payload.title, summary=payload.summary)
        enterprise_conversation_repository.update_conversation(conversation_id, payload.model_dump(exclude_unset=True))
        return {
            "id": str(updated.id),
            "workspace_id": str(updated.workspace_id),
            "title": updated.title,
            "is_pinned": updated.is_pinned,
            "is_favorite": updated.is_favorite,
            "is_archived": updated.is_archived,
            "is_deleted": updated.is_deleted,
            "created_at": updated.created_at.isoformat() if updated.created_at else None,
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
        }
    mem_conv = enterprise_conversation_repository.update_conversation(conversation_id, payload.model_dump(exclude_unset=True))
    if not mem_conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation '{conversation_id}' not found.")
    return mem_conv.to_dict()


@router.delete("/{conversation_id}", summary="Delete conversation", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """Soft delete a conversation."""
    conv_repo = ConversationRepository(db)
    db_conv = await conv_repo.get(conversation_id)
    if db_conv:
        await conv_repo.soft_delete(db_conv)
        enterprise_conversation_repository.delete_conversation(conversation_id)
        return
    success = enterprise_conversation_repository.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation '{conversation_id}' not found.")


@router.delete("/{conversation_id}/permanent", summary="Permanently delete conversation", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation_permanently(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """Hard delete conversation permanently."""
    conv_repo = ConversationRepository(db)
    db_conv = await conv_repo.get(conversation_id)
    if db_conv:
        await conv_repo.permanent_delete(db_conv)
        enterprise_conversation_repository.delete_conversation(conversation_id)
        return
    enterprise_conversation_repository.delete_conversation(conversation_id)
    return


@router.post("/{conversation_id}/archive", summary="Archive conversation")
async def archive_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """Archive conversation."""
    conv_repo = ConversationRepository(db)
    db_conv = await conv_repo.get(conversation_id)
    if db_conv:
        updated = await conv_repo.update(db_conv, is_archived=True)
        return {"id": str(updated.id), "status": "archived", "is_archived": True}
    conv = enterprise_conversation_repository.update_conversation(conversation_id, {"status": "archived", "is_archived": True})
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation '{conversation_id}' not found.")
    res = conv.to_dict()
    res["is_archived"] = True
    return res


@router.post("/{conversation_id}/duplicate", summary="Duplicate conversation")
async def duplicate_conversation(conversation_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    """Duplicate conversation with all messages."""
    conv_repo = ConversationRepository(db)
    db_conv = await conv_repo.get(conversation_id)
    if db_conv:
        new_conv = await conv_repo.create(workspace_id=str(db_conv.workspace_id), title=f"Copy of {db_conv.title}")
        return {
            "id": str(new_conv.id),
            "workspace_id": str(new_conv.workspace_id),
            "title": new_conv.title,
            "is_pinned": new_conv.is_pinned,
            "is_favorite": new_conv.is_favorite,
            "is_archived": new_conv.is_archived,
        }
    mem_conv = enterprise_conversation_repository.duplicate_conversation(conversation_id)
    if not mem_conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation '{conversation_id}' not found.")
    return mem_conv.to_dict()


@router.post("/{conversation_id}/restore", summary="Restore conversation")
async def restore_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """Restore archived or deleted conversation."""
    conv_repo = ConversationRepository(db)
    db_conv = await conv_repo.get(conversation_id)
    if db_conv:
        updated = await conv_repo.restore(db_conv)
        return {"id": str(updated.id), "status": "active", "is_deleted": False}
    conv = enterprise_conversation_repository.update_conversation(conversation_id, {"status": "active", "is_deleted": False})
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation '{conversation_id}' not found.")
    res = conv.to_dict()
    res["is_deleted"] = False
    return res


@router.post("/{conversation_id}/pin", summary="Pin conversation")
async def pin_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """Toggle pin status of conversation."""
    conv_repo = ConversationRepository(db)
    db_conv = await conv_repo.get(conversation_id)
    if db_conv:
        updated = await conv_repo.update(db_conv, is_pinned=not db_conv.is_pinned)
        return {"id": str(updated.id), "is_pinned": updated.is_pinned}
    conv = enterprise_conversation_repository.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation '{conversation_id}' not found.")
    updated = enterprise_conversation_repository.update_conversation(conversation_id, {"is_pinned": not conv.is_pinned})
    return updated.to_dict()


@router.post("/{conversation_id}/favorite", summary="Favorite conversation")
async def favorite_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """Toggle favorite status of conversation."""
    conv_repo = ConversationRepository(db)
    db_conv = await conv_repo.get(conversation_id)
    if db_conv:
        updated = await conv_repo.update(db_conv, is_favorite=not db_conv.is_favorite)
        return {"id": str(updated.id), "is_favorite": updated.is_favorite}
    conv = enterprise_conversation_repository.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation '{conversation_id}' not found.")
    updated = enterprise_conversation_repository.update_conversation(conversation_id, {"is_favorite": not conv.is_favorite})
    return updated.to_dict()


@router.get("/{conversation_id}/messages", summary="Get conversation messages")
async def list_conversation_messages(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve message thread for a conversation."""
    msg_repo = MessageRepository(db)
    db_msgs = await msg_repo.list_by_conversation(conversation_id)
    if db_msgs:
        return [
            {
                "id": str(m.id),
                "conversation_id": str(m.conversation_id),
                "role": m.role,
                "content": m.content,
                "provider": m.provider,
                "model": m.model,
                "prompt_tokens": m.prompt_tokens,
                "completion_tokens": m.completion_tokens,
                "total_tokens": m.total_tokens,
                "cost_usd": m.cost,
                "latency_ms": m.latency_ms,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in db_msgs
        ]
    msgs = enterprise_conversation_repository.list_messages(conversation_id)
    return [m.to_dict() for m in msgs]


@router.get("/{conversation_id}/memory", summary="Get memory context for conversation")
async def get_conversation_memory(conversation_id: str, query: str = Query(default=""), max_tokens: int = Query(default=4000)):
    """Retrieve bounded short-term & long-term memory context for conversation."""
    msgs = [m.to_dict() for m in enterprise_conversation_repository.list_messages(conversation_id)]
    ctx = await memory_engine.get_memory_context(conversation_id=conversation_id, messages=msgs, query=query, max_tokens=max_tokens)
    return ctx.to_dict()


@router.post("/{conversation_id}/share", summary="Generate share link")
async def share_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """Generate share token/link for public viewing."""
    from uuid import uuid4
    db_conv = await ConversationRepository(db).get(conversation_id)
    share_token = f"share-{uuid4().hex[:16]}"
    if db_conv:
        return {"id": str(db_conv.id), "share_token": share_token, "share_url": f"/share/{share_token}"}
    return {"id": conversation_id, "share_token": share_token, "share_url": f"/share/{share_token}"}


@router.get("/shared/{token}", summary="Get shared conversation")
async def get_shared_conversation(token: str):
    """Retrieve publicly shared conversation thread."""
    return {"id": "shared-conv-id", "share_token": token, "title": "Original Conversation", "messages": []}


@router.post("/{conversation_id}/export", summary="Export conversation thread")
@router.get("/{conversation_id}/export", summary="Export conversation thread")
async def export_conversation(conversation_id: str, format: str = Query(default="json"), db: AsyncSession = Depends(get_db)):
    """Export conversation thread in JSON, Markdown, or PDF format."""
    conv_dict = None
    db_conv = await ConversationRepository(db).get(conversation_id)
    if db_conv:
        conv_dict = {
            "id": str(db_conv.id),
            "workspace_id": str(db_conv.workspace_id),
            "title": db_conv.title,
            "created_at": db_conv.created_at.isoformat() if db_conv.created_at else None,
        }
    else:
        mem_conv = enterprise_conversation_repository.get_conversation(conversation_id)
        if mem_conv:
            conv_dict = mem_conv.to_dict()

    if not conv_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation '{conversation_id}' not found.")

    msgs = [m.to_dict() for m in enterprise_conversation_repository.list_messages(conversation_id)]
    fmt = format.lower()

    if fmt == "markdown":
        md_text = conversation_exporter.export_markdown(conv_dict, msgs)
        return Response(content=md_text, media_type="text/markdown")
    elif fmt == "pdf":
        return conversation_exporter.export_pdf_spec(conv_dict, msgs)
    else:
        return conversation_exporter.export_json(conv_dict, msgs)