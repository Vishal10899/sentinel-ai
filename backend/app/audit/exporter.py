import csv
import io
import json
from typing import Any

from app.audit.models import AuditRecord


class AuditExporter:
    """Exports audit logs to CSV or JSON format for compliance archiving."""

    def export_json(self, records: list[AuditRecord]) -> str:
        """Export audit records as formatted JSON string."""
        return json.dumps([r.to_dict() for r in records], indent=2)

    def export_csv(self, records: list[AuditRecord]) -> str:
        """Export audit records as CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "ID", "Timestamp", "User ID", "User Name", "Workspace ID",
            "Action", "Resource", "Old Value", "New Value", "IP Address",
            "Status", "Severity", "Correlation ID"
        ])

        for r in records:
            writer.writerow([
                r.id, r.timestamp, r.user_id, r.user_name, r.workspace_id,
                r.action, r.resource, r.old_value or "", r.new_value or "",
                r.ip_address, r.status, r.severity, r.correlation_id or ""
            ])

        return output.getvalue()


audit_exporter = AuditExporter()
