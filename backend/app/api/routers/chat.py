from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import current_user
from app.chat.dto import (
    ChatRequest,
    ChatResponse,
    ConversationMessagesResponse,
)
from app.chat.service import chat_service
from app.db.session import get_db
from app.models.user import User
from app.repositories import ConversationRepository, MessageRepository, WorkspaceRepository

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
async def generate(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    workspace = await WorkspaceRepository(db).get_or_create_for_user(user.id, user.name)
    body.workspace_id = str(workspace.id)
    return await chat_service.generate(
        body,
        db,
    )


@router.post(
    "/stream",
    summary="Stream chat completion via SSE",
)
async def stream_generate(
    http_request: Request,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    workspace = await WorkspaceRepository(db).get_or_create_for_user(user.id, user.name)
    body.workspace_id = str(workspace.id)
    return StreamingResponse(
        chat_service.stream_generate(body, db=db, request=http_request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/stream/{stream_id}/cancel",
    summary="Immediately cancel an active stream session",
)
async def cancel_stream(
    stream_id: str,
    user: User = Depends(current_user),
):
    from app.streaming.manager import stream_manager
    cancelled = stream_manager.cancel_session(stream_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Active stream session not found")
    return {"status": "success", "message": f"Stream {stream_id} cancellation signal sent"}


@router.get(
    "/stream/active",
    summary="List active streaming sessions for workspace",
)
async def list_active_streams(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    from app.streaming.manager import stream_manager
    workspace = await WorkspaceRepository(db).get_by_owner(user.id)
    if workspace is None:
        return []
    return stream_manager.list_active_sessions(workspace_id=str(workspace.id))


@router.get(
    "/{conversation_id}/messages",
    response_model=ConversationMessagesResponse,
)
async def get_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    workspace = await WorkspaceRepository(db).get_by_owner(user.id)
    conversation = await ConversationRepository(db).get(conversation_id)
    if workspace is None or conversation is None or str(conversation.workspace_id) != str(workspace.id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await chat_service.get_messages(
        conversation_id,
        db,
        conversation=conversation,
    )


@router.delete(
    "/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete single message",
)
async def delete_message(
    message_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    msg_repo = MessageRepository(db)
    msg = await msg_repo.get(message_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="Message not found")
    await msg_repo.delete(msg)
