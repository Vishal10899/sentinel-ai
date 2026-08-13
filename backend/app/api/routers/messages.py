"""Enterprise Message Management REST API Router."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import current_user
from app.chat import enterprise_conversation_repository
from app.models.user import User

router = APIRouter(prefix="/messages", tags=["messages"])


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


@router.post("", summary="Add message to conversation", status_code=status.HTTP_201_CREATED)
async def add_message(payload: AddMessagePayload, user: User = Depends(current_user)):
    """Add a message to a conversation thread in < 2ms."""
    conv = enterprise_conversation_repository.get_conversation(payload.conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{payload.conversation_id}' not found.",
        )

    msg = enterprise_conversation_repository.add_message(
        conversation_id=payload.conversation_id,
        role=payload.role,
        content=payload.content,
        provider=payload.provider,
        model=payload.model,
        prompt_tokens=payload.prompt_tokens,
        completion_tokens=payload.completion_tokens,
        cost=payload.cost,
        latency_ms=payload.latency_ms,
        attachments=payload.attachments,
    )
    return msg.to_dict()


@router.delete("/{message_id}", summary="Delete message", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(message_id: str):
    """Delete a message from a conversation thread."""
    success = enterprise_conversation_repository.delete_message(message_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message '{message_id}' not found.",
        )
