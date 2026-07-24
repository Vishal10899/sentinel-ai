from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    conversation_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    prompt: str = Field(min_length=1, max_length=32_000)
    model: str | None = None
    workspace_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    provider: str
    model: str | None = None
    response: str
    latency_ms: int
    created_at: datetime

class MessageItem(BaseModel):
    role: str
    content: str
    provider: str | None = None
    model: str | None = None
    latency_ms: int = 0
    created_at: datetime


class ConversationMessagesResponse(BaseModel):
    conversation_id: str
    messages: list[MessageItem]
