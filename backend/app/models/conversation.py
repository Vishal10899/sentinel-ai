from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="New Conversation",
    )

    is_pinned: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    is_favorite: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    is_archived: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    share_token: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    summary: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    tags: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    metadata_json: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )