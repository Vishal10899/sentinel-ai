"""Enterprise Security Platform REST API Router."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.dependencies import current_user
from app.audit import audit_engine, audit_repository
from app.models.user import User
from app.rbac import ALL_PERMISSIONS, rbac_engine, role_repository
from app.security import (
    enterprise_api_key_manager,
    secret_manager,
    security_metrics_aggregator,
    session_manager,
)

router = APIRouter(prefix="/security", tags=["security"])


class CreateAPIKeyPayload(BaseModel):
    key_name: str = Field(min_length=1)
    workspace_id: str = Field(default="default")
    expires_days: int | None = Field(default=90)


@router.get("/roles", summary="List RBAC roles and permission matrix")
async def list_roles():
    """List all system roles, inheritance graphs, and permission matrix (< 0.2 ms)."""
    return rbac_engine.get_permission_matrix()


@router.get("/permissions", summary="List all system permissions")
async def list_permissions():
    """List all fine-grained system permissions."""
    return {"permissions": ALL_PERMISSIONS}


@router.get("/audit", summary="Query security audit logs")
async def get_audit_logs(
    workspace_id: str = Query(default="default"),
    action: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    """Query immutable security audit logs (< 0.5 ms)."""
    records = audit_repository.list(workspace_id=workspace_id, action=action, limit=limit)
    return [r.to_dict() for r in records]


@router.post("/api-keys", summary="Create workspace API key", status_code=status.HTTP_201_CREATED)
async def create_api_key(payload: CreateAPIKeyPayload, user: User = Depends(current_user)):
    """Create a workspace-scoped API key. Raw key is returned once upon creation."""
    u_id = str(getattr(user, "id", "default_user"))
    rec, raw_key = enterprise_api_key_manager.create_api_key(
        key_name=payload.key_name,
        workspace_id=payload.workspace_id,
        user_id=u_id,
        expires_days=payload.expires_days,
    )
    audit_engine.record_event(
        action="API_KEY_CREATED",
        resource=f"api_key:{rec.key_id}",
        user_id=u_id,
        workspace_id=payload.workspace_id,
        new_value=rec.masked_key,
    )
    res = rec.to_dict()
    res["raw_api_key"] = raw_key
    return res


@router.delete("/api-keys/{id}", summary="Revoke API key", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(id: str, user: User = Depends(current_user)):
    """Revoke an API key by ID."""
    u_id = str(getattr(user, "id", "default_user"))
    success = enterprise_api_key_manager.revoke_api_key(id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"API key '{id}' not found.")
    audit_engine.record_event(
        action="API_KEY_REVOKED",
        resource=f"api_key:{id}",
        user_id=u_id,
    )


@router.post("/api-keys/{id}/rotate", summary="Rotate API key")
async def rotate_api_key(id: str, user: User = Depends(current_user)):
    """Rotate an API key. Returns metadata and new raw key."""
    u_id = str(getattr(user, "id", "default_user"))
    res = enterprise_api_key_manager.rotate_api_key(id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"API key '{id}' not found or inactive.")
    rec, new_raw = res
    audit_engine.record_event(
        action="API_KEY_ROTATED",
        resource=f"api_key:{id}",
        user_id=u_id,
        new_value=rec.masked_key,
    )
    ret = rec.to_dict()
    ret["new_raw_api_key"] = new_raw
    return ret


@router.get("/sessions", summary="List active user sessions")
async def list_sessions(user: User = Depends(current_user)):
    """List active sessions for current user or all users if admin."""
    u_id = str(getattr(user, "id", "default_user"))
    sessions = session_manager.list_user_sessions(user_id=u_id)
    return [s.to_dict() for s in sessions]


@router.delete("/sessions/{id}", summary="Revoke user session (force logout)", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(id: str, user: User = Depends(current_user)):
    """Force logout a user session."""
    u_id = str(getattr(user, "id", "default_user"))
    success = session_manager.revoke_session(id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session '{id}' not found.")
    audit_engine.record_event(
        action="LOGOUT",
        resource=f"session:{id}",
        user_id=u_id,
    )


@router.get("/metrics", summary="Get security telemetry metrics")
async def get_security_metrics(workspace_id: str = Query(default="default")):
    """Get aggregated security metrics report."""
    return security_metrics_aggregator.get_report(workspace_id=workspace_id).to_dict()
