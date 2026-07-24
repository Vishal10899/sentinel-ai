from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.dto import (
    ChatRequest,
    ChatResponse,
    ConversationMessagesResponse,
)
from app.chat.service import chat_service
from app.api.dependencies import current_user
from app.auth.service import User
from app.db.session import get_db
from app.repositories import ConversationRepository, WorkspaceRepository

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
async def generate(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    workspace = await WorkspaceRepository(db).get_by_owner(user.id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    request.workspace_id = str(workspace.id)
    return await chat_service.generate(
        request,
        db,
    )


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
    )
