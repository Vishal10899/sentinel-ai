"""Virtual API Key Management & Authorization Router."""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import current_user, require_permission
from app.models.user import User
from app.security.keys import VirtualKeyType
from app.security.repository import virtual_key_repository

router = APIRouter(prefix="/virtual-keys", tags=["virtual-keys"])


class CreateVirtualKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    workspace_id: str = "default"
    key_type: VirtualKeyType = VirtualKeyType.WORKSPACE
    allowed_providers: list[str] = Field(default_factory=list)
    allowed_models: list[str] = Field(default_factory=list)
    expires_in_seconds: int | None = None


@router.get("", summary="List Virtual API Keys")
async def list_virtual_keys(workspace_id: str | None = Query(default=None), user: User = Depends(current_user)):
    """List Virtual API Keys for workspace."""
    keys = virtual_key_repository.list_keys(workspace_id=workspace_id)
    return [k.to_dict() for k in keys]


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a new Virtual API Key")
async def create_virtual_key(request: CreateVirtualKeyRequest, user: User = Depends(require_permission("apikey.manage"))):
    """Generate a new secure Virtual API Key. Returns raw secret token once upon creation."""
    raw_secret, key_obj = virtual_key_repository.create_key(
        workspace_id=request.workspace_id,
        name=request.name,
        key_type=request.key_type,
        allowed_providers=request.allowed_providers,
        allowed_models=request.allowed_models,
        expires_in_seconds=request.expires_in_seconds,
    )
    res = key_obj.to_dict()
    res["secret_key"] = raw_secret  # Secret key returned only on creation
    return res


@router.get("/{key_id}", summary="Get Virtual Key by ID")
async def get_virtual_key(key_id: str, user: User = Depends(current_user)):
    """Retrieve Virtual Key metadata."""
    key_obj = virtual_key_repository.get_key(key_id)
    if not key_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Virtual Key not found")
    return key_obj.to_dict()


@router.post("/{key_id}/rotate", summary="Rotate Virtual API Key")
async def rotate_virtual_key(key_id: str, user: User = Depends(require_permission("apikey.manage"))):
    """Rotate secret token for a Virtual API Key while preserving permissions."""
    rotated = virtual_key_repository.rotate_key(key_id)
    if not rotated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Virtual Key not found")
    raw_secret, new_key_obj = rotated
    res = new_key_obj.to_dict()
    res["secret_key"] = raw_secret
    return res


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke Virtual API Key")
async def revoke_virtual_key(key_id: str, user: User = Depends(require_permission("apikey.manage"))):
    """Revoke a Virtual API Key."""
    revoked = virtual_key_repository.revoke_key(key_id)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Virtual Key not found")
    return {"status": "success", "message": "Virtual API Key revoked successfully."}
