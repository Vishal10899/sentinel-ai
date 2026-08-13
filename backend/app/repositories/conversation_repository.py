from datetime import datetime
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        workspace_id: str,
        title: str = "New Conversation",
        tags: str | None = None,
    ) -> Conversation:
        from app.models.workspace import Workspace
        from app.models.user import User

        ws_res = await self.db.execute(select(Workspace).where(Workspace.id == workspace_id))
        ws = ws_res.scalar_one_or_none()
        if ws is None:
            ws_any_res = await self.db.execute(select(Workspace).where(Workspace.is_active.is_(True)))
            ws_any = ws_any_res.scalars().first()
            if ws_any:
                workspace_id = ws_any.id
            else:
                user_res = await self.db.execute(select(User).where(User.id == "default_user"))
                def_user = user_res.scalar_one_or_none()
                if not def_user:
                    def_user = User(
                        id="default_user",
                        name="System User",
                        email="system@sentinel.ai",
                        salt="default_salt",
                        password_hash="default_hash",
                    )
                    self.db.add(def_user)
                    await self.db.flush()

                def_ws = Workspace(
                    id="default",
                    name="Default Workspace",
                    slug="default",
                    owner_id=def_user.id,
                    is_active=True,
                )
                self.db.add(def_ws)
                await self.db.flush()
                workspace_id = "default"

        conversation = Conversation(
            workspace_id=workspace_id,
            title=title,
            tags=tags,
        )
        self.db.add(conversation)
        await self.db.commit()
        return conversation

    async def get(
        self,
        conversation_id: str,
    ) -> Conversation | None:
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_share_token(self, share_token: str) -> Conversation | None:
        result = await self.db.execute(
            select(Conversation).where(Conversation.share_token == share_token)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        workspace_id: str,
        query: str | None = None,
        is_pinned: bool | None = None,
        is_favorite: bool | None = None,
        is_archived: bool | None = False,
        is_deleted: bool | None = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Conversation]:
        stmt = select(Conversation).where(Conversation.workspace_id == workspace_id)
        if is_deleted is not None:
            stmt = stmt.where(Conversation.is_deleted == is_deleted)
        if is_archived is not None:
            stmt = stmt.where(Conversation.is_archived == is_archived)
        if is_pinned is not None:
            stmt = stmt.where(Conversation.is_pinned == is_pinned)
        if is_favorite is not None:
            stmt = stmt.where(Conversation.is_favorite == is_favorite)
        if query and query.strip():
            pattern = f"%{query.strip()}%"
            stmt = stmt.where(Conversation.title.ilike(pattern))

        stmt = stmt.order_by(
            Conversation.is_pinned.desc(),
            Conversation.is_favorite.desc(),
            Conversation.updated_at.desc(),
        )
        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        conversation: Conversation,
        title: str | None = None,
        is_pinned: bool | None = None,
        is_favorite: bool | None = None,
        is_archived: bool | None = None,
        is_deleted: bool | None = None,
        tags: str | None = None,
        summary: str | None = None,
        metadata_json: str | None = None,
    ) -> Conversation:
        if title is not None:
            conversation.title = title
        if is_pinned is not None:
            conversation.is_pinned = is_pinned
        if is_favorite is not None:
            conversation.is_favorite = is_favorite
        if is_archived is not None:
            conversation.is_archived = is_archived
        if is_deleted is not None:
            conversation.is_deleted = is_deleted
            conversation.deleted_at = datetime.utcnow() if is_deleted else None
        if tags is not None:
            conversation.tags = tags
        if summary is not None:
            conversation.summary = summary
        if metadata_json is not None:
            conversation.metadata_json = metadata_json

        conversation.updated_at = datetime.utcnow()
        await self.db.commit()
        return conversation

    async def duplicate(self, conversation_id: str, new_title: str | None = None) -> Conversation:
        original = await self.get(conversation_id)
        if not original:
            raise ValueError("Conversation not found")

        duplicated = Conversation(
            workspace_id=original.workspace_id,
            title=new_title or f"Copy of {original.title}",
            tags=original.tags,
            metadata_json=original.metadata_json,
        )
        self.db.add(duplicated)
        await self.db.flush()

        # Copy all messages
        msgs_res = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        messages = list(msgs_res.scalars().all())

        for msg in messages:
            new_msg = Message(
                conversation_id=duplicated.id,
                role=msg.role,
                content=msg.content,
                provider=msg.provider,
                model=msg.model,
                system_prompt=msg.system_prompt,
                attachments=msg.attachments,
                strategy_used=msg.strategy_used,
                routing_explanation_json=msg.routing_explanation_json,
                prompt_tokens=msg.prompt_tokens,
                completion_tokens=msg.completion_tokens,
                total_tokens=msg.total_tokens,
                cost=msg.cost,
                latency_ms=msg.latency_ms,
            )
            self.db.add(new_msg)

        await self.db.commit()
        return duplicated

    async def soft_delete(self, conversation: Conversation) -> Conversation:
        return await self.update(conversation, is_deleted=True)

    async def restore(self, conversation: Conversation) -> Conversation:
        conversation.is_deleted = False
        conversation.deleted_at = None
        conversation.is_archived = False
        conversation.updated_at = datetime.utcnow()
        await self.db.commit()
        return conversation

    async def permanent_delete(self, conversation: Conversation) -> None:
        await self.db.delete(conversation)
        await self.db.commit()

    async def generate_share_token(self, conversation: Conversation) -> str:
        if not conversation.share_token:
            conversation.share_token = f"share_{uuid4().hex}"
            conversation.updated_at = datetime.utcnow()
            await self.db.commit()
        return conversation.share_token