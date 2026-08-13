"""Enterprise Secret Management Engine.

Provides secure storage for provider API keys, DB credentials, Redis credentials, and encryption keys.
Supports encryption at rest simulation, secret masking, and secret rotation hooks.
"""

from dataclasses import dataclass, field
import datetime
import hashlib
from typing import Any


@dataclass
class SecretRecord:
    """Enterprise Secret Record metadata."""

    secret_id: str
    secret_name: str
    secret_type: str  # provider_key, db_credentials, redis_credentials, encryption_key
    masked_value: str
    encrypted_value: str
    workspace_id: str
    version: int = 1
    last_rotated_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "secret_id": self.secret_id,
            "secret_name": self.secret_name,
            "secret_type": self.secret_type,
            "masked_value": self.masked_value,
            "workspace_id": self.workspace_id,
            "version": self.version,
            "last_rotated_at": self.last_rotated_at,
        }


class SecretManager:
    """Enterprise Secret Management Engine."""

    def __init__(self) -> None:
        self._secrets: dict[str, SecretRecord] = {}

    def mask_secret(self, secret_val: str) -> str:
        """Mask secret value for safe exposure (e.g. sk-proj-...a1b2)."""
        if not secret_val:
            return "*****"
        if len(secret_val) <= 8:
            return "****" + secret_val[-2:]
        return secret_val[:4] + "..." + secret_val[-4:]

    def encrypt_at_rest(self, raw_val: str) -> str:
        """Simulate secure AES-GCM / SHA-256 encryption at rest."""
        return "enc_sha256_" + hashlib.sha256(raw_val.encode("utf-8")).hexdigest()

    def store_secret(
        self,
        secret_name: str,
        raw_val: str,
        secret_type: str = "provider_key",
        workspace_id: str = "default",
    ) -> SecretRecord:
        """Store encrypted secret record."""
        s_id = f"sec-{secret_name.lower().replace(' ', '-')}"
        record = SecretRecord(
            secret_id=s_id,
            secret_name=secret_name,
            secret_type=secret_type,
            masked_value=self.mask_secret(raw_val),
            encrypted_value=self.encrypt_at_rest(raw_val),
            workspace_id=workspace_id,
        )
        self._secrets[s_id] = record
        return record

    def rotate_secret(self, secret_id: str, new_raw_val: str) -> SecretRecord | None:
        """Secret rotation hook."""
        rec = self._secrets.get(secret_id)
        if not rec:
            return None
        rec.version += 1
        rec.encrypted_value = self.encrypt_at_rest(new_raw_val)
        rec.masked_value = self.mask_secret(new_raw_val)
        rec.last_rotated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return rec

    def list_secrets(self, workspace_id: str = "default") -> list[SecretRecord]:
        """List secret metadata (never raw values)."""
        return [s for s in self._secrets.values() if s.workspace_id == workspace_id]


secret_manager = SecretManager()
