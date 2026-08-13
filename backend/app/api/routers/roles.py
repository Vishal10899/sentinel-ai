"""Enterprise RBAC Roles & Permissions Management API Router."""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import current_user, require_permission
from app.models.user import User
from app.rbac.engine import rbac_engine
from app.rbac.repository import role_repository

router = APIRouter(prefix="/roles", tags=["roles"])


class CreateRoleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    permissions: list[str] = Field(default_factory=list)


class UpdateRoleRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None


class AssignRoleRequest(BaseModel):
    user_id: str
    role_id: str


@router.get("", summary="List all roles")
async def list_roles(user: User = Depends(current_user)):
    """List all built-in and custom roles."""
    roles = role_repository.list_roles()
    return [r.to_dict() for r in roles]


@router.get("/permissions/matrix", summary="Get permission capabilities matrix")
async def get_permission_matrix(user: User = Depends(current_user)):
    """Retrieve complete permission capabilities matrix mapping roles to permissions."""
    return rbac_engine.get_permission_matrix()


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create custom role")
async def create_role(request: CreateRoleRequest, user: User = Depends(require_permission("users.manage"))):
    """Create a new custom role with assigned permission scopes."""
    role = role_repository.create_role(
        name=request.name,
        description=request.description,
        permissions=request.permissions,
    )
    return role.to_dict()


@router.get("/{role_id}", summary="Get role details")
async def get_role(role_id: str, user: User = Depends(current_user)):
    """Retrieve detailed role metadata and permissions."""
    role = role_repository.get_role(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role.to_dict()


@router.put("/{role_id}", summary="Update custom role")
async def update_role(role_id: str, request: UpdateRoleRequest, user: User = Depends(require_permission("users.manage"))):
    """Update custom role permissions and metadata."""
    updated = role_repository.update_role(
        role_id=role_id,
        name=request.name,
        description=request.description,
        permissions=request.permissions,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found or is a protected built-in role")
    return updated.to_dict()


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete custom role")
async def delete_role(role_id: str, user: User = Depends(require_permission("users.manage"))):
    """Delete a custom role."""
    deleted = role_repository.delete_role(role_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found or is a protected built-in role")


@router.get("/users/{user_id}/permissions", summary="Get user effective permissions")
async def get_user_permissions(user_id: str, user: User = Depends(current_user)):
    """Retrieve effective permissions for a user based on role assignment and inheritance."""
    role = role_repository.get_user_role(user_id)
    effective_permissions = rbac_engine.get_user_effective_permissions(user_id)
    return {
        "user_id": user_id,
        "role": role.to_dict(),
        "effective_permissions": effective_permissions,
    }


@router.post("/assign", summary="Assign role to user")
async def assign_role(request: AssignRoleRequest, user: User = Depends(require_permission("users.manage"))):
    """Assign a role to a user and return updated effective permissions."""
    assigned = role_repository.assign_user_role(user_id=request.user_id, role_id=request.role_id)
    if not assigned:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    effective_permissions = rbac_engine.get_user_effective_permissions(request.user_id)
    return {
        "status": "success",
        "message": f"Role '{request.role_id}' assigned to user '{request.user_id}'",
        "user_id": request.user_id,
        "role_id": request.role_id,
        "effective_permissions": effective_permissions,
    }


