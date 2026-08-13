import hashlib
import hmac
import secrets
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class VirtualKeyType(str, Enum):
    WORKSPACE = "WORKSPACE"
    SERVICE = "SERVICE"
    TEMPORARY = "TEMPORARY"
    READONLY = "READONLY"


@dataclass
class VirtualKey:
    """Enterprise Virtual API Key concealing real provider credentials."""

    id: str
    workspace_id: str
    name: str
    key_hash: str
    prefix: str
    key_type: VirtualKeyType = VirtualKeyType.WORKSPACE
    allowed_providers: list[str] = field(default_factory=list)
    allowed_models: list[str] = field(default_factory=list)
    max_tokens_limit: int | None = None
    monthly_budget_usd: float | None = None
    current_spend_usd: float = 0.0
    rate_limit_rpm: int = 600  # Requests Per Minute
    is_active: bool = True
    expires_at: float | None = None
    created_at: float = field(default_factory=time.time)
    last_used_at: float | None = None
    usage_count: int = 0

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def verify_secret(self, secret: str) -> bool:
        """Constant-time security hash verification against secret token."""
        computed_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()
        return hmac.compare_digest(self.key_hash, computed_hash)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["key_type"] = self.key_type.value
        del d["key_hash"]  # Never expose key hash
        return d

    @classmethod
    def generate(
        cls,
        key_id: str,
        workspace_id: str,
        name: str,
        key_type: VirtualKeyType = VirtualKeyType.WORKSPACE,
        allowed_providers: list[str] | None = None,
        allowed_models: list[str] | None = None,
        expires_in_seconds: int | None = None,
    ) -> tuple[str, "VirtualKey"]:
        """Generate a new secure Virtual Key pair. Returns (raw_secret_token, VirtualKey)."""
        random_bytes = secrets.token_hex(24)
        raw_secret = f"sk-snt-live-{random_bytes}"
        key_hash = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()
        prefix = raw_secret[:16] + "..."

        expires_at = (time.time() + expires_in_seconds) if expires_in_seconds else None

        vk = cls(
            id=key_id,
            workspace_id=workspace_id,
            name=name,
            key_hash=key_hash,
            prefix=prefix,
            key_type=key_type,
            allowed_providers=allowed_providers or [],
            allowed_models=allowed_models or [],
            expires_at=expires_at,
        )
        return raw_secret, vk
