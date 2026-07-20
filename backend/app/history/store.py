"""Process-local history used by the MVP API."""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from collections import defaultdict
import secrets


@dataclass(slots=True)
class HistoryItem:
    request_id: str
    prompt: str
    provider_id: str
    model_id: str
    response: str
    estimated_cost_usd: str
    latency_ms: int
    created_at: str


class HistoryStore:
    def __init__(self):
        self._items = defaultdict(list)

    def add(self, user_id, **values):
        item = HistoryItem(
            secrets.token_urlsafe(9),
            created_at=datetime.now(timezone.utc).isoformat(),
            **values,
        )
        self._items[user_id].insert(0, item)
        return item

    def list(self, user_id, query=""):
        return [
            asdict(item)
            for item in self._items[user_id]
            if query.lower() in item.prompt.lower()
        ]


history_store = HistoryStore()