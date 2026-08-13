"""Enterprise Workspace API Key Management Engine.

Provides SHA-256 hashed API Key storage, creation, rotation, revocation, and usage tracking.
Never exposes raw API keys after initial creation.
"""

from dataclasses import dataclass, field
import datetime
import hashlib
import time
from typing import Any
import uuid


@dataclass
class EnterpriseAPIKeyRecord:
    """Enterprise API Key Metadata Record."""

    key_id: str
    key_name: str
    workspace_id: str
    user_id: str
    key_hash: str
    masked_key: str
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    last_used_at: str | None = None
    is_active: bool = True
    usage_count: int = 0
    expires_at_ts: float | None = None

    def to_dict(self) -> dict:
        return {
            "key_id": self.key_id,
            "key_name": self.key_name,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "masked_key": self.masked_key,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "is_active": self.is_active,
            "usage_count": self.usage_count,
        }


class EnterpriseAPIKeyManager:
    """Enterprise API Key Management Engine."""

    def __init__(self) -> None:
        self._keys: dict[str, EnterpriseAPIKeyRecord] = {}

    def _hash_key(self, raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def create_api_key(
        self,
        key_name: str,
        workspace_id: str = "default",
        user_id: str = "default_user",
        expires_days: int | None = 90,
    ) -> tuple[EnterpriseAPIKeyRecord, str]:
        """Create a workspace-scoped API key. Returns (metadata_record, raw_key)."""
        raw_key = f"sentinel_sec_{uuid.uuid4().hex}"
        key_id = f"key-{uuid.uuid4().hex[:12]}"
        masked = f"sentinel_sec_{raw_key[13:17]}...{raw_key[-4:]}"
        exp_ts = time.time() + (expires_days * 86400) if expires_days else None

        rec = EnterpriseAPIKeyRecord(
            key_id=key_id,
            key_name=key_name,
            workspace_id=workspace_id,
            user_id=user_id,
            key_hash=self._hash_key(raw_key),
            masked_key=masked,
            expires_at_ts=exp_ts,
        )
        self._keys[key_id] = rec
        return rec, raw_key

    def rotate_api_key(self, key_id: str) -> tuple[EnterpriseAPIKeyRecord, str] | None:
        """Rotate API key while preserving key_id and metadata."""
        rec = self._keys.get(key_id)
        if not rec or not rec.is_active:
            return None

        new_raw_key = f"sentinel_sec_{uuid.uuid4().hex}"
        rec.key_hash = self._hash_key(new_raw_key)
        rec.masked_key = f"sentinel_sec_{new_raw_key[13:17]}...{new_raw_key[-4:]}"
        rec.created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return rec, new_raw_key

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke API key."""
        rec = self._keys.get(key_id)
        if rec:
            rec.is_active = False
            return True
        return False

    def list_api_keys(self, workspace_id: str = "default") -> list[EnterpriseAPIKeyRecord]:
        """List active API keys for workspace."""
        return [k for k in self._keys.values() if k.workspace_id == workspace_id and k.is_active]


enterprise_api_key_manager = EnterpriseAPIKeyManager()
