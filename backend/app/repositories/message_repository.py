from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        conversation_id: str,
        role: str,
        content: str,
        provider: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
        attachments: str | None = None,
        strategy_used: str | None = None,
        routing_explanation_json: str | None = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        cost: float = 0,
        latency_ms: int = 0,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            provider=provider,
            model=model,
            system_prompt=system_prompt,
            attachments=attachments,
            strategy_used=strategy_used,
            routing_explanation_json=routing_explanation_json,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            latency_ms=latency_ms,
        )
        self.db.add(message)
        await self.db.commit()
        return message

    async def get(self, message_id: str) -> Message | None:
        result = await self.db.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        message: Message,
        content: str | None = None,
        role: str | None = None,
    ) -> Message:
        if content is not None:
            message.content = content
        if role is not None:
            message.role = role
        await self.db.commit()
        return message

    async def list_by_conversation(
        self,
        conversation_id: str,
        limit: int | None = None,
    ) -> list[Message]:
        stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete(
        self,
        message: Message,
    ) -> None:
        await self.db.delete(message)
        await self.db.commit()