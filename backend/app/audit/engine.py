import time
from uuid import uuid4
from typing import Any

from app.audit.models import AuditRecord
from app.audit.repository import AuditRepository, audit_repository


class AuditEngine:
    """Enterprise Audit Engine emitting immutable audit event records."""

    def __init__(self, repository: AuditRepository | None = None) -> None:
        self.repository = repository or audit_repository

    def record_event(
        self,
        action: str,
        resource: str,
        user_id: str = "system",
        user_name: str = "System Admin",
        workspace_id: str = "default",
        old_value: str | None = None,
        new_value: str | None = None,
        status: str = "SUCCESS",
        severity: str = "INFO",
        correlation_id: str | None = None,
    ) -> AuditRecord:
        """Create and persist an immutable audit log record."""
        record = AuditRecord(
            id=str(uuid4()),
            user_id=user_id,
            user_name=user_name,
            workspace_id=workspace_id,
            action=action,
            resource=resource,
            timestamp=time.time(),
            old_value=old_value,
            new_value=new_value,
            status=status,
            severity=severity,
            correlation_id=correlation_id or str(uuid4())[:8],
        )
        return self.repository.log(record)


audit_engine = AuditEngine()
