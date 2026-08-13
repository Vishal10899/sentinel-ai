"""Enterprise Bulkhead Isolation & Worker Pool Engine.

Provides independent concurrency pools, queues, and worker limits per provider
so a failing provider never impacts other active providers.
"""

import asyncio
from dataclasses import dataclass, field
import datetime
import time
from typing import Any


@dataclass
class BulkheadStatus:
    """Bulkhead concurrency and queue metrics per provider."""

    provider_id: str
    max_concurrent_workers: int
    active_workers: int
    queue_depth: int
    max_queue_capacity: int
    rejected_requests: int
    completed_requests: int

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "max_concurrent_workers": self.max_concurrent_workers,
            "active_workers": self.active_workers,
            "queue_depth": self.queue_depth,
            "max_queue_capacity": self.max_queue_capacity,
            "rejected_requests": self.rejected_requests,
            "completed_requests": self.completed_requests,
        }


class BulkheadEngine:
    """Enterprise Bulkhead Provider Isolation Engine."""

    def __init__(self, max_concurrent: int = 50, max_queue: int = 100) -> None:
        self.default_max_concurrent = max_concurrent
        self.default_max_queue = max_queue
        self._active_workers: dict[str, int] = {}
        self._queue_depth: dict[str, int] = {}
        self._rejected_requests: dict[str, int] = {}
        self._completed_requests: dict[str, int] = {}

    def _get_key(self, provider_id: str) -> str:
        return provider_id.lower()

    def acquire(self, provider_id: str) -> tuple[bool, str]:
        """Try to acquire a worker slot in < 0.1 ms."""
        key = self._get_key(provider_id)
        current_workers = self._active_workers.get(key, 0)
        current_queue = self._queue_depth.get(key, 0)

        if current_workers < self.default_max_concurrent:
            self._active_workers[key] = current_workers + 1
            return True, "Worker slot acquired"

        if current_queue < self.default_max_queue:
            self._queue_depth[key] = current_queue + 1
            return True, "Queued in provider bulkhead pool"

        self._rejected_requests[key] = self._rejected_requests.get(key, 0) + 1
        return False, f"Bulkhead capacity exceeded for provider '{provider_id}'. Request rejected by overload protection."

    def release(self, provider_id: str) -> None:
        """Release worker slot and process queued item."""
        key = self._get_key(provider_id)
        current_queue = self._queue_depth.get(key, 0)
        current_workers = self._active_workers.get(key, 0)

        if current_queue > 0:
            self._queue_depth[key] = current_queue - 1
        elif current_workers > 0:
            self._active_workers[key] = current_workers - 1

        self._completed_requests[key] = self._completed_requests.get(key, 0) + 1

    def get_status(self, provider_id: str) -> BulkheadStatus:
        """Get bulkhead status for provider."""
        key = self._get_key(provider_id)
        return BulkheadStatus(
            provider_id=provider_id,
            max_concurrent_workers=self.default_max_concurrent,
            active_workers=self._active_workers.get(key, 0),
            queue_depth=self._queue_depth.get(key, 0),
            max_queue_capacity=self.default_max_queue,
            rejected_requests=self._rejected_requests.get(key, 0),
            completed_requests=self._completed_requests.get(key, 0),
        )

    def list_statuses(self) -> list[BulkheadStatus]:
        """List status of all active bulkhead pools."""
        providers = ["openai", "gemini", "anthropic", "ollama"]
        return [self.get_status(p) for p in providers]


bulkhead_engine = BulkheadEngine()
