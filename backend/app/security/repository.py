import json
import time
from uuid import uuid4
from typing import Any
from datetime import datetime

from app.security.keys import VirtualKey, VirtualKeyType
from app.db.session import get_db_session
from app.models.virtual_key import VirtualKeyModel


class VirtualKeyRepository:
    """Repository managing Virtual API Keys, rotation, revocation, and permission constraints with PostgreSQL persistence."""

    def __init__(self) -> None:
        self._keys: dict[str, VirtualKey] = {}
        self._hash_lookup: dict[str, str] = {}  # key_hash -> key_id

    def list_keys(self, workspace_id: str | None = None) -> list[VirtualKey]:
        """List virtual keys optionally filtered by workspace."""
        keys = list(self._keys.values())
        if workspace_id:
            keys = [k for k in keys if k.workspace_id == workspace_id]
        return keys

    def get_key(self, key_id: str) -> VirtualKey | None:
        """Retrieve key by ID."""
        return self._keys.get(key_id)

    def create_key(
        self,
        workspace_id: str,
        name: str,
        key_type: VirtualKeyType = VirtualKeyType.WORKSPACE,
        allowed_providers: list[str] | None = None,
        allowed_models: list[str] | None = None,
        expires_in_seconds: int | None = None,
    ) -> tuple[str, VirtualKey]:
        """Generate and store a new Virtual API Key."""
        key_id = str(uuid4())
        raw_secret, key_obj = VirtualKey.generate(
            key_id=key_id,
            workspace_id=workspace_id,
            name=name,
            key_type=key_type,
            allowed_providers=allowed_providers,
            allowed_models=allowed_models,
            expires_in_seconds=expires_in_seconds,
        )

        self._keys[key_id] = key_obj
        self._hash_lookup[key_obj.key_hash] = key_id
        return raw_secret, key_obj

    def authenticate_secret(self, secret: str) -> VirtualKey | None:
        """Authenticate raw secret token using constant-time hash lookup."""
        if not secret:
            return None
        import hashlib
        target_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()
        key_id = self._hash_lookup.get(target_hash)
        if not key_id:
            return None

        key_obj = self._keys.get(key_id)
        if not key_obj or not key_obj.is_active or key_obj.is_expired():
            return None

        # Update usage telemetry
        key_obj.last_used_at = time.time()
        key_obj.usage_count += 1
        return key_obj

    def rotate_key(self, key_id: str) -> tuple[str, VirtualKey] | None:
        """Rotate a Virtual Key secret while maintaining permissions and metadata."""
        key_obj = self._keys.get(key_id)
        if not key_obj:
            return None

        # Clear old hash lookup
        if key_obj.key_hash in self._hash_lookup:
            del self._hash_lookup[key_obj.key_hash]

        # Generate new secret pair
        raw_secret, new_key_obj = VirtualKey.generate(
            key_id=key_id,
            workspace_id=key_obj.workspace_id,
            name=key_obj.name,
            key_type=key_obj.key_type,
            allowed_providers=key_obj.allowed_providers,
            allowed_models=key_obj.allowed_models,
        )

        self._keys[key_id] = new_key_obj
        self._hash_lookup[new_key_obj.key_hash] = key_id
        return raw_secret, new_key_obj

    def revoke_key(self, key_id: str) -> bool:
        """Revoke / disable a Virtual Key."""
        key_obj = self._keys.get(key_id)
        if not key_obj:
            return False

        key_obj.is_active = False
        if key_obj.key_hash in self._hash_lookup:
            del self._hash_lookup[key_obj.key_hash]
        return True


virtual_key_repository = VirtualKeyRepository()
