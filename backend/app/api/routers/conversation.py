from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import current_user
from app.api.schemas import (
    CreateConversationRequest,
    ConversationResponse,
)
from app.auth.service import User
from app.db.session import get_db
from app.repositories import (
    ConversationRepository,
    WorkspaceRepository,
)

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


@router.post(
    "",
    response_model=ConversationResponse,
)
async def create_conversation(
    request: CreateConversationRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):

    workspace = await WorkspaceRepository(db).get_by_owner(
        user.id
    )

    if workspace is None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
        )

    conversation = await ConversationRepository(
        db
    ).create(
        workspace_id=workspace.id,
        title=request.title,
    )

    return conversation


@router.get(
    "",
    response_model=list[ConversationResponse],
)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):

    workspace = await WorkspaceRepository(db).get_by_owner(
        user.id
    )

    if workspace is None:
        return []

    return await ConversationRepository(
        db
    ).list(workspace.id)