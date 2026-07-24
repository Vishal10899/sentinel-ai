from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        workspace_id: str,
        title: str = "New Conversation",
    ) -> Conversation:

        conversation = Conversation(
            workspace_id=workspace_id,
            title=title,
        )

        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def get(
        self,
        conversation_id: str,
    ) -> Conversation | None:

        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id
            )
        )

        return result.scalar_one_or_none()

    async def list(
        self,
        workspace_id: str,
    ) -> list[Conversation]:

        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.workspace_id == workspace_id
            )
            .order_by(
                Conversation.created_at.desc()
            )
        )

        return list(result.scalars().all())

    async def update_title(
        self,
        conversation: Conversation,
        title: str,
    ) -> Conversation:

        conversation.title = title

        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def delete(
        self,
        conversation: Conversation,
    ) -> None:

        await self.db.delete(conversation)
        await self.db.commit()