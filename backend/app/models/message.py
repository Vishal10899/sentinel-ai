from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    provider: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    system_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    attachments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    strategy_used: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    routing_explanation_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    prompt_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    completion_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    total_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    cost: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    latency_ms: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )