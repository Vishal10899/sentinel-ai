"""Enterprise Security Telemetry & Metrics Aggregator.

Tracks active sessions, failed logins, permission denials, API key usage, secret rotation status, and audit events.
Integrates directly with Sentinel AI Observability.
"""

from dataclasses import dataclass, field
import time
from typing import Any

from app.audit.repository import audit_repository
from app.rbac import rbac_engine
from app.security.api_keys import enterprise_api_key_manager
from app.security.secrets import secret_manager
from app.security.sessions import session_manager


@dataclass
class SecurityMetricsReport:
    """Aggregated Security Telemetry Report."""

    active_sessions: int
    failed_logins: int
    permission_denials: int
    active_api_keys: int
    total_secrets: int
    recent_audit_events: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_sessions": self.active_sessions,
            "failed_logins": self.failed_logins,
            "permission_denials": self.permission_denials,
            "active_api_keys": self.active_api_keys,
            "total_secrets": self.total_secrets,
            "recent_audit_events": self.recent_audit_events,
        }


class SecurityMetricsAggregator:
    """Enterprise Security Telemetry Aggregator."""

    def __init__(self) -> None:
        self.failed_login_count: int = 0
        self.permission_denial_count: int = 0

    def record_failed_login(self) -> None:
        self.failed_login_count += 1

    def record_permission_denial(self) -> None:
        self.permission_denial_count += 1

    def get_report(self, workspace_id: str = "default") -> SecurityMetricsReport:
        """Generate comprehensive security metrics report."""
        active_sess = len(session_manager.list_user_sessions())
        api_keys = len(enterprise_api_key_manager.list_api_keys(workspace_id=workspace_id))
        secrets = len(secret_manager.list_secrets(workspace_id=workspace_id))
        audit_events = len(audit_repository.list(workspace_id=workspace_id))

        return SecurityMetricsReport(
            active_sessions=active_sess,
            failed_logins=self.failed_login_count,
            permission_denials=self.permission_denial_count,
            active_api_keys=api_keys,
            total_secrets=secrets,
            recent_audit_events=audit_events,
        )


security_metrics_aggregator = SecurityMetricsAggregator()
