"""High-Performance Enterprise Conversation & Message Repository.

Enforces sub-2ms conversation creation & message insertion and sub-10ms conversation loading.
"""

from dataclasses import dataclass, field
import datetime
import time
from typing import Any
import uuid


@dataclass
class EnterpriseConversation:
    """Enterprise Conversation domain object."""

    conversation_id: str
    workspace_id: str
    user_id: str
    title: str
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    last_activity_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    total_messages: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    current_model: str = "gemini-2.0-flash"
    current_provider: str = "gemini"
    status: str = "active"  # active, archived, deleted
    is_pinned: bool = False
    is_favorite: bool = False
    tags: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "id": self.conversation_id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_activity_at": self.last_activity_at,
            "total_messages": self.total_messages,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "current_model": self.current_model,
            "current_provider": self.current_provider,
            "status": self.status,
            "is_pinned": self.is_pinned,
            "is_favorite": self.is_favorite,
            "is_archived": self.status == "archived",
            "is_deleted": self.status == "deleted",
            "tags": list(self.tags),
            "summary": self.summary,
        }


@dataclass
class EnterpriseMessage:
    """Enterprise Message domain object."""

    message_id: str
    conversation_id: str
    role: str  # user, assistant, system, tool
    content: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    provider: str = "gemini"
    model: str = "gemini-2.0-flash"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    tokens: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0
    attachments: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "id": self.message_id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "tokens": self.tokens,
            "token_usage": {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.tokens,
            },
            "cost": self.cost,
            "latency_ms": self.latency_ms,
            "attachments": list(self.attachments),
            "metadata": self.metadata,
        }


class EnterpriseConversationRepository:
    """High-performance Conversation & Message Repository (< 2ms creation/insert, < 10ms load)."""

    def __init__(self) -> None:
        self._conversations: dict[str, EnterpriseConversation] = {}
        self._messages: dict[str, list[EnterpriseMessage]] = {}

    def create_conversation(
        self,
        workspace_id: str = "default",
        user_id: str = "default_user",
        title: str = "New Enterprise Conversation",
        description: str = "",
        provider: str = "gemini",
        model: str = "gemini-2.0-flash",
        tags: list[str] | None = None,
    ) -> EnterpriseConversation:
        """Create a new conversation record in < 2ms."""
        c_id = f"conv-{uuid.uuid4().hex[:12]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conv = EnterpriseConversation(
            conversation_id=c_id,
            workspace_id=workspace_id,
            user_id=user_id,
            title=title,
            description=description,
            created_at=now,
            updated_at=now,
            last_activity_at=now,
            current_provider=provider,
            current_model=model,
            tags=tuple(tags or []),
        )
        self._conversations[c_id] = conv
        self._messages[c_id] = []
        return conv

    def get_conversation(self, conversation_id: str) -> EnterpriseConversation | None:
        """Get conversation record in < 10ms."""
        return self._conversations.get(conversation_id)

    def list_conversations(
        self,
        workspace_id: str | None = None,
        user_id: str | None = None,
        status: str | None = None,
        is_pinned: bool | None = None,
        is_favorite: bool | None = None,
        limit: int = 100,
    ) -> list[EnterpriseConversation]:
        """List and filter conversations."""
        convs = list(reversed(list(self._conversations.values())))
        if workspace_id:
            convs = [c for c in convs if c.workspace_id == workspace_id]
        if user_id:
            convs = [c for c in convs if c.user_id == user_id]
        if status:
            convs = [c for c in convs if c.status == status]
        if is_pinned is not None:
            convs = [c for c in convs if c.is_pinned == is_pinned]
        if is_favorite is not None:
            convs = [c for c in convs if c.is_favorite == is_favorite]
        return convs[:limit]

    def update_conversation(self, conversation_id: str, updates: dict[str, Any]) -> EnterpriseConversation | None:
        """Update conversation properties."""
        conv = self.get_conversation(conversation_id)
        if not conv:
            return None
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conv.updated_at = now
        conv.last_activity_at = now

        for k in ("title", "description", "current_model", "current_provider", "status", "is_pinned", "is_favorite", "summary"):
            if k in updates and updates[k] is not None:
                setattr(conv, k, updates[k])
        if "tags" in updates and updates["tags"] is not None:
            conv.tags = tuple(updates["tags"])
        return conv

    def delete_conversation(self, conversation_id: str) -> bool:
        """Soft delete conversation."""
        conv = self.get_conversation(conversation_id)
        if conv:
            conv.status = "deleted"
            return True
        return False

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        provider: str = "gemini",
        model: str = "gemini-2.0-flash",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost: float = 0.0,
        latency_ms: float = 0.0,
        attachments: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EnterpriseMessage:
        """Insert a message and update conversation statistics in < 2ms."""
        m_id = f"msg-{uuid.uuid4().hex[:12]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        t_tokens = prompt_tokens + completion_tokens
        if t_tokens == 0:
            t_tokens = max(len(content) // 4, 1)

        msg = EnterpriseMessage(
            message_id=m_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            timestamp=now,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            tokens=t_tokens,
            cost=cost,
            latency_ms=latency_ms,
            attachments=tuple(attachments or []),
            metadata=metadata or {},
        )

        if conversation_id not in self._messages:
            self._messages[conversation_id] = []
        self._messages[conversation_id].append(msg)

        # Update parent conversation totals
        conv = self.get_conversation(conversation_id)
        if conv:
            conv.total_messages += 1
            conv.total_tokens += t_tokens
            conv.total_cost += cost
            conv.last_activity_at = now
            conv.current_provider = provider
            conv.current_model = model

        return msg

    def list_messages(self, conversation_id: str) -> list[EnterpriseMessage]:
        """List messages for a conversation."""
        return list(self._messages.get(conversation_id, []))

    def delete_message(self, message_id: str) -> bool:
        """Delete a message."""
        for c_id, msgs in self._messages.items():
            for idx, m in enumerate(msgs):
                if m.message_id == message_id:
                    del msgs[idx]
                    return True
        return False

    def get_workspace_statistics(self, workspace_id: str = "default") -> dict[str, Any]:
        """Calculate workspace-isolated conversation and token statistics."""
        convs = [c for c in self._conversations.values() if c.workspace_id == workspace_id]
        total_convs = len(convs)
        total_msgs = sum(c.total_messages for c in convs)
        total_tokens = sum(c.total_tokens for c in convs)
        total_cost = round(sum(c.total_cost for c in convs), 6)

        return {
            "workspace_id": workspace_id,
            "total_conversations": total_convs,
            "active_conversations": len([c for c in convs if c.status == "active"]),
            "archived_conversations": len([c for c in convs if c.status == "archived"]),
            "pinned_conversations": len([c for c in convs if c.is_pinned]),
            "favorite_conversations": len([c for c in convs if c.is_favorite]),
            "total_messages": total_msgs,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
        }


enterprise_conversation_repository = EnterpriseConversationRepository()
