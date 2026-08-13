"""Enterprise Audit Logs & Compliance Search API Router."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.dependencies import current_user, require_permission
from app.audit.exporter import audit_exporter
from app.audit.repository import audit_repository
from app.models.user import User

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", summary="Search audit logs")
async def search_audit_logs(
    workspace_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    query: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    user: User = Depends(require_permission("audit.read")),
):
    """Search and filter immutable audit logs across user, action, severity, and workspace parameters."""
    records = audit_repository.search(
        workspace_id=workspace_id,
        user_id=user_id,
        action=action,
        severity=severity,
        query=query,
        limit=limit,
    )
    return [r.to_dict() for r in records]


@router.get("/stats", summary="Get audit telemetry and activity stats")
async def get_audit_stats(
    workspace_id: str | None = Query(default=None),
    user: User = Depends(require_permission("audit.read")),
):
    """Retrieve audit statistics, top actions, user activity breakdowns, and severity counts."""
    return audit_repository.get_stats(workspace_id=workspace_id)


@router.get("/export", summary="Export audit logs as CSV or JSON")
async def export_audit_logs(
    format: str = Query(default="csv", pattern="^(csv|json)$"),
    workspace_id: str | None = Query(default=None),
    user: User = Depends(require_permission("audit.read")),
):

    """Export audit records for SOC 2 / ISO 27001 compliance archiving."""
    records = audit_repository.search(workspace_id=workspace_id, limit=5000)

    if format == "json":
        json_content = audit_exporter.export_json(records)
        return Response(content=json_content, media_type="application/json", headers={"Content-Disposition": 'attachment; filename="sentinel_audit_logs.json"'})
    else:
        csv_content = audit_exporter.export_csv(records)
        return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="sentinel_audit_logs.csv"'})
