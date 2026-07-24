from time import perf_counter

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.dto import ChatRequest
from app.providers.manager import provider_manager
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository


class ChatService:

    async def generate(
        self,
        data: ChatRequest,
        db: AsyncSession,
    ):

        message_repository = MessageRepository(db)
        conversation_repository = ConversationRepository(db)

        # Check conversation
        conversation = await conversation_repository.get(
            data.conversation_id
        )

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        if data.workspace_id and str(conversation.workspace_id) != data.workspace_id:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Check provider
        try:
            provider = provider_manager.get(data.provider)

        except KeyError:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{data.provider}' not found",
            )

        # Save user message
        await message_repository.create(
            conversation_id=data.conversation_id,
            role="user",
            content=data.prompt,
            provider=data.provider,
            model=data.model,
        )

        # Generate AI response and record observed backend latency.
        started_at = perf_counter()
        try:
            response = await provider.generate(
                prompt=data.prompt,
                model=data.model,
            )

        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"{provider.name} provider error: {str(e)}",
            )

        latency_ms = round((perf_counter() - started_at) * 1000)

        # Save assistant message
        assistant_message = await message_repository.create(
            conversation_id=data.conversation_id,
            role="assistant",
            content=response,
            provider=data.provider,
            model=data.model,
            latency_ms=latency_ms,
        )

        return {
            "conversation_id": str(data.conversation_id),
            "provider": provider.name,
            "model": data.model,
            "response": response,
            "latency_ms": latency_ms,
            "created_at": assistant_message.created_at,
        }

    async def get_messages(
        self,
        conversation_id: str,
        db: AsyncSession,
    ):

        conversation_repository = ConversationRepository(db)

        conversation = await conversation_repository.get(
            conversation_id
        )

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        message_repository = MessageRepository(db)

        messages = await message_repository.list_by_conversation(
            conversation_id
        )

        return {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                    "provider": message.provider,
                    "model": message.model,
                    "latency_ms": message.latency_ms,
                    "created_at": message.created_at,
                }
                for message in messages
            ],
        }


chat_service = ChatService()
