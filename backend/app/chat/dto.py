from datetime import datetime

from pydantic import BaseModel, Field


class AttachmentItem(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    extracted_text: str | None = None
    url: str | None = None


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    provider: str | None = None
    model: str | None = None
    prompt: str = Field(min_length=1, max_length=32_000)
    system_prompt: str | None = None
    strategy: str = "balanced"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1024, ge=1, le=32000)
    attachments: list[AttachmentItem] | None = None
    workspace_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    provider: str
    model: str | None = None
    response: str
    latency_ms: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    strategy_used: str | None = None
    routing_explanation: dict | None = None
    created_at: datetime


class MessageItem(BaseModel):
    id: str | None = None
    role: str
    content: str
    provider: str | None = None
    model: str | None = None
    system_prompt: str | None = None
    attachments: list[AttachmentItem] | None = None
    strategy_used: str | None = None
    routing_explanation: dict | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    created_at: datetime


class ConversationMessagesResponse(BaseModel):
    conversation_id: str
    messages: list[MessageItem]
