import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CacheEntry:
    """Enterprise AI Memory Record (Improvement 4 & 5)."""

    key: str
    workspace_id: str
    prompt: str
    normalized_prompt: str
    response_text: str
    provider_id: str
    model_id: str
    estimated_cost_usd: float
    latency_ms: float
    total_tokens: int
    created_at: float = 0.0
    ttl_seconds: int = 86400  # 24 hours default
    metadata_json: str | None = None

    # Improvement 4 & 5 Extended Enterprise Metadata
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    prompt_hash: str = ""
    embedding: list[float] | None = None
    embedding_id: str | None = None
    conversation_id: str | None = None
    last_used: float = 0.0
    use_count: int = 0
    cache_source: str = "ai_memory"
    confidence: float = 0.90
    quality_score: float = 0.90
    similarity: float = 1.0
    version: str = "v2.0"
    freshness_status: str = "VALID"
    execution_status: str = "SUCCESS"
    state: str = "CREATED"  # CREATED, ACTIVE, FREQUENTLY_USED, AGING, EXPIRED, ARCHIVED
    fingerprint: dict[str, Any] = field(default_factory=dict)
    successful_reuses: int = 0
    rejected_reuses: int = 0

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = time.time()
        if not self.last_used:
            self.last_used = self.created_at
        if not self.prompt_hash:
            self.prompt_hash = self.key

    def is_expired(self) -> bool:
        """Check if entry TTL has passed."""
        if self.ttl_seconds <= 0:
            return False
        return (time.time() - self.created_at) > self.ttl_seconds

    def update_lifecycle_state(self) -> str:
        """Evaluate lifecycle state (Improvement 5)."""
        now = time.time()
        if self.is_expired():
            self.state = "EXPIRED"
        elif self.use_count >= 5 or self.quality_score >= 0.95:
            self.state = "FREQUENTLY_USED"
        elif (now - self.last_used) > 43200:  # 12 hours idle
            self.state = "AGING"
        else:
            self.state = "ACTIVE"
        return self.state

    def to_dict(self) -> dict[str, Any]:
        self.update_lifecycle_state()
        d = asdict(self)
        # Exclude raw float vector from simple dict if large
        if d.get("embedding"):
            d["embedding_dim"] = len(d["embedding"])
            d["embedding"] = None
        return d


class CacheStore:
    """Enterprise Thread-Safe Memory Store with Lifecycle Management & Eviction Protection."""

    def __init__(self, max_entries: int = 10000) -> None:
        self.max_entries = max_entries
        self._store: dict[str, CacheEntry] = {}

    def get(self, key: str) -> CacheEntry | None:
        """Retrieve entry if exists and not expired."""
        entry = self._store.get(key)
        if not entry:
            return None
        if entry.is_expired():
            del self._store[key]
            return None
        entry.update_lifecycle_state()
        return entry

    def set(self, entry: CacheEntry) -> None:
        """Store memory record, protecting FREQUENTLY_USED memories from LRU eviction."""
        if len(self._store) >= self.max_entries and entry.key not in self._store:
            # Candidate keys to evict (exclude FREQUENTLY_USED memories unless all are frequently used)
            candidates = [k for k, e in self._store.items() if e.update_lifecycle_state() != "FREQUENTLY_USED"]
            if not candidates:
                candidates = list(self._store.keys())
            
            oldest_key = min(candidates, key=lambda k: self._store[k].last_used)
            del self._store[oldest_key]

        now = time.time()
        if not entry.created_at:
            entry.created_at = now
        entry.last_used = now
        entry.update_lifecycle_state()
        self._store[entry.key] = entry

    def list_entries(self, workspace_id: str | None = None) -> list[CacheEntry]:
        """List active unexpired cache memories."""
        valid = []
        expired_keys = []

        for key, entry in self._store.items():
            if entry.is_expired():
                expired_keys.append(key)
            elif workspace_id is None or entry.workspace_id == workspace_id:
                entry.update_lifecycle_state()
                valid.append(entry)

        for k in expired_keys:
            del self._store[k]

        return valid

    def clear(self, workspace_id: str | None = None) -> int:
        """Clear cache entries for a workspace or clear all."""
        if workspace_id is None:
            count = len(self._store)
            self._store.clear()
            return count

        keys_to_del = [k for k, v in self._store.items() if v.workspace_id == workspace_id]
        for k in keys_to_del:
            del self._store[k]
        return len(keys_to_del)
