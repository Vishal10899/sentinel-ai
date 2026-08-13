import asyncio
import logging
from typing import Any

from app.providers.base import BaseProvider
from app.providers.manager import provider_manager
from app.streaming.session import StreamSession

logger = logging.getLogger("sentinel.streaming")


class StreamManager:
    """Centralized Stream Manager handling stream lifecycles, cancellation, timeouts, failover, and metrics."""

    def __init__(self) -> None:
        self._sessions: dict[str, StreamSession] = {}

    def create_session(
        self,
        conversation_id: str,
        workspace_id: str,
        provider: str,
        model: str,
        routing_strategy: str = "balanced",
        stream_id: str | None = None,
    ) -> StreamSession:
        """Initialize and register an enterprise stream session."""
        session = StreamSession(
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            provider=provider,
            model=model,
            routing_strategy=routing_strategy,
            stream_id=stream_id,
        )
        self._sessions[session.stream_id] = session
        logger.info(
            f"[StreamManager] Stream session created: {session.stream_id} (conv: {conversation_id}, provider: {provider}, model: {model})"
        )
        return session

    def get_session(self, stream_id: str) -> StreamSession | None:
        """Retrieve active stream session by stream_id."""
        return self._sessions.get(stream_id)

    def cancel_session(self, stream_id: str) -> bool:
        """Request immediate cancellation of a stream session."""
        session = self._sessions.get(stream_id)
        if session:
            session.cancel()
            logger.info(f"[StreamManager] Stream session cancelled: {stream_id}")
            return True
        return False

    def cleanup_session(self, stream_id: str) -> None:
        """Remove completed or cancelled stream session from memory."""
        if stream_id in self._sessions:
            del self._sessions[stream_id]
            logger.info(f"[StreamManager] Stream session cleaned up: {stream_id}")

    def list_active_sessions(self, workspace_id: str | None = None) -> list[dict[str, Any]]:
        """List active streaming sessions, optionally filtered by workspace."""
        active = []
        for s in list(self._sessions.values()):
            if workspace_id is None or s.workspace_id == workspace_id:
                active.append(s.to_dict())
        return active

    def get_failover_provider(self, current_provider: str) -> BaseProvider | None:
        """Resolve failover target adapter if streaming fails initially."""
        return provider_manager.get_failover_provider(current_provider)


# Process-scoped singleton manager instance
stream_manager = StreamManager()
