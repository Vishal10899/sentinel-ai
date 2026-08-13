"""Enterprise Idempotency & Replay Engine.

Prevents duplicate execution and replays previous responses for identical idempotency keys.
"""

from dataclasses import dataclass, field
import datetime
from typing import Any


@dataclass
class IdempotencyRecord:
    """Idempotency execution record."""

    key: str
    workspace_id: str
    user_id: str
    response_payload: dict[str, Any]
    status_code: int = 200
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "response_payload": self.response_payload,
            "status_code": self.status_code,
            "created_at": self.created_at,
        }


class IdempotencyEngine:
    """Enterprise Idempotency Engine (< 0.1 ms lookup)."""

    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}

    def _get_key(self, idempotency_key: str, workspace_id: str) -> str:
        return f"{workspace_id}:{idempotency_key}"

    def get_record(self, idempotency_key: str, workspace_id: str = "default") -> IdempotencyRecord | None:
        """Lookup previous execution by idempotency key (< 0.1 ms)."""
        if not idempotency_key:
            return None
        key = self._get_key(idempotency_key, workspace_id)
        return self._records.get(key)

    def save_record(
        self,
        idempotency_key: str,
        response_payload: dict[str, Any],
        workspace_id: str = "default",
        user_id: str = "default_user",
        status_code: int = 200,
    ) -> IdempotencyRecord:
        """Save execution result for idempotency key."""
        key = self._get_key(idempotency_key, workspace_id)
        rec = IdempotencyRecord(
            key=idempotency_key,
            workspace_id=workspace_id,
            user_id=user_id,
            response_payload=response_payload,
            status_code=status_code,
        )
        self._records[key] = rec
        return rec


idempotency_engine = IdempotencyEngine()
