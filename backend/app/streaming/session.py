import asyncio
from typing import Any
from uuid import uuid4

from app.streaming.metrics import StreamMetrics


class StreamSession:
    """Manages state, cancellation signals, and metrics for an individual streaming request."""

    def __init__(
        self,
        conversation_id: str,
        workspace_id: str,
        provider: str,
        model: str,
        routing_strategy: str = "balanced",
        stream_id: str | None = None,
    ) -> None:
        self.stream_id = stream_id or str(uuid4())
        self.conversation_id = conversation_id
        self.workspace_id = workspace_id
        self.provider = provider
        self.model = model
        self.routing_strategy = routing_strategy
        self.cancel_event = asyncio.Event()
        self.metrics = StreamMetrics(
            stream_id=self.stream_id,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            provider=provider,
            model=model,
            routing_strategy=routing_strategy,
        )

    def cancel(self) -> None:
        """Trigger cancellation signal for this active stream."""
        self.cancel_event.set()
        self.metrics.cancelled = True

    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self.cancel_event.is_set()

    def to_dict(self) -> dict[str, Any]:
        """Serialize session state for API inspection."""
        return {
            "stream_id": self.stream_id,
            "conversation_id": self.conversation_id,
            "workspace_id": self.workspace_id,
            "provider": self.provider,
            "model": self.model,
            "routing_strategy": self.routing_strategy,
            "cancelled": self.is_cancelled(),
            "first_token_latency_ms": self.metrics.first_token_latency_ms,
            "total_tokens": self.metrics.total_tokens,
            "tokens_per_second": self.metrics.tokens_per_second,
            "estimated_cost": self.metrics.estimated_cost,
        }
