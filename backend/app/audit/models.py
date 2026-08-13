import time
from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class AuditRecord:
    """Immutable Audit Log Record for security governance and SOC 2 / ISO 27001 compliance."""

    id: str
    user_id: str
    user_name: str
    workspace_id: str
    action: str
    resource: str
    timestamp: float = field(default_factory=time.time)
    old_value: str | None = None
    new_value: str | None = None
    ip_address: str = "127.0.0.1"
    user_agent: str = "Sentinel-AI/1.0"
    status: str = "SUCCESS"  # SUCCESS, DENIED, FAILED
    severity: str = "INFO"   # INFO, WARNING, CRITICAL
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
