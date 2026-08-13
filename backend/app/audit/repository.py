"""Repository storing immutable audit records and providing multi-criteria search filtering."""

import time
from typing import Any
from uuid import uuid4

from app.audit.models import AuditRecord


class AuditRepository:
    """Repository storing immutable audit records and providing multi-criteria search filtering."""

    def __init__(self, max_records: int = 25000) -> None:
        self.max_records = max_records
        self._records: list[AuditRecord] = []

    def log(self, record: AuditRecord) -> AuditRecord:
        """Store an immutable audit record."""
        if len(self._records) >= self.max_records:
            self._records.pop(0)  # FIFO eviction if capacity reached
        self._records.append(record)
        return record

    def search(
        self,
        workspace_id: str | None = None,
        user_id: str | None = None,
        action: str | None = None,
        severity: str | None = None,
        query: str | None = None,
        limit: int = 100,
    ) -> list[AuditRecord]:
        """Search and filter audit logs."""
        results = list(reversed(self._records))  # Newest first

        if workspace_id:
            results = [r for r in results if r.workspace_id == workspace_id]
        if user_id:
            results = [r for r in results if r.user_id == user_id]
        if action:
            results = [r for r in results if r.action.lower() == action.lower()]
        if severity:
            results = [r for r in results if r.severity.lower() == severity.lower()]
        if query:
            q = query.lower()
            results = [
                r for r in results
                if q in r.action.lower() or q in r.resource.lower() or q in r.user_name.lower()
            ]

        return results[:limit]

    def list(
        self,
        workspace_id: str | None = None,
        user_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[AuditRecord]:
        """Alias for search method."""
        return self.search(workspace_id=workspace_id, user_id=user_id, action=action, limit=limit)

    def get_stats(self, workspace_id: str | None = None) -> dict[str, Any]:
        """Calculate audit log statistics."""
        records = self.search(workspace_id=workspace_id, limit=10000)
        total = len(records)
        action_breakdown: dict[str, int] = {}
        user_breakdown: dict[str, int] = {}
        severity_breakdown: dict[str, int] = {}

        for r in records:
            action_breakdown[r.action] = action_breakdown.get(r.action, 0) + 1
            user_breakdown[r.user_name] = user_breakdown.get(r.user_name, 0) + 1
            severity_breakdown[r.severity] = severity_breakdown.get(r.severity, 0) + 1

        return {
            "total_audit_events": total,
            "top_actions": action_breakdown,
            "top_users": user_breakdown,
            "severity_counts": severity_breakdown,
        }


audit_repository = AuditRepository()
