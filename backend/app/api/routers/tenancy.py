"""Enterprise Multi-Tenant Workspaces, Organizations, and Identity REST API Router."""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import current_user, require_permission
from app.models.user import User
from app.tenancy.engine import tenancy_engine
from app.tenancy.repository import tenancy_repository

router = APIRouter(tags=["tenancy"])


class CreateOrgRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=50)
    domain: str = Field(min_length=1, max_length=100)


class CreateWorkspaceRequest(BaseModel):
    org_id: str = "org-default"
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=50)
    description: str = ""


class InviteMemberRequest(BaseModel):
    org_id: str = "org-default"
    workspace_id: str = "default"
    email: str = Field(min_length=3, max_length=100)
    role_id: str = "role-developer"


class AcceptInvitationRequest(BaseModel):
    token: str


class ConfigureSSORequest(BaseModel):
    provider_type: str = Field(pattern="^(SAML|OIDC|OKTA|AZURE_AD|GOOGLE_WORKSPACE)$")
    issuer_url: str = Field(min_length=5)
    client_id: str = Field(min_length=3)


class UpdateProfileRequest(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    timezone: str | None = None
    language: str | None = None


# --- Organizations APIs ---
@router.get("/organizations", summary="List organizations")
async def list_organizations(user: User = Depends(current_user)):
    """List all enterprise organizations."""
    orgs = tenancy_repository.list_organizations()
    return [o.to_dict() for o in orgs]


@router.post("/organizations", status_code=status.HTTP_201_CREATED, summary="Create organization")
async def create_organization(request: CreateOrgRequest, user: User = Depends(require_permission("workspace.manage"))):
    """Create a new multi-tenant organization."""
    org = tenancy_engine.create_organization(
        name=request.name,
        slug=request.slug,
        domain=request.domain,
        owner_id=user.id,
    )
    return org.to_dict()


@router.get("/organizations/{org_id}", summary="Get organization by ID")
async def get_organization(org_id: str, user: User = Depends(current_user)):
    """Retrieve organization metadata."""
    org = tenancy_repository.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org.to_dict()


# --- Workspaces APIs ---
@router.get("/workspaces", summary="List tenant workspaces")
async def list_workspaces(org_id: str | None = Query(default=None), user: User = Depends(current_user)):
    """List isolated tenant workspaces."""
    workspaces = tenancy_repository.list_workspaces(org_id=org_id)
    return [w.to_dict() for w in workspaces]


@router.post("/workspaces", status_code=status.HTTP_201_CREATED, summary="Create tenant workspace")
async def create_workspace(request: CreateWorkspaceRequest, user: User = Depends(require_permission("workspace.manage"))):
    """Create an isolated workspace within an organization."""
    ws = tenancy_engine.create_workspace(
        org_id=request.org_id,
        name=request.name,
        slug=request.slug,
        description=request.description,
        owner_id=user.id,
    )
    return ws.to_dict()


# --- Members & Invitations APIs ---
@router.get("/organizations/{org_id}/members", summary="List organization members")
async def list_org_members(org_id: str, user: User = Depends(current_user)):
    """List members assigned to organization."""
    mems = tenancy_repository.list_members(org_id=org_id)
    return [m.to_dict() for m in mems]


@router.post("/organizations/{org_id}/invitations", status_code=status.HTTP_201_CREATED, summary="Issue member invitation")
async def invite_member(org_id: str, request: InviteMemberRequest, user: User = Depends(require_permission("workspace.manage"))):
    """Issue member invitation token."""
    inv = tenancy_engine.invite_member(
        org_id=org_id,
        workspace_id=request.workspace_id,
        email=request.email,
        role_id=request.role_id,
        inviter_user_id=user.id,
    )
    return inv.to_dict()


@router.post("/invitations/accept", summary="Accept invitation token")
async def accept_invitation(request: AcceptInvitationRequest, user: User = Depends(current_user)):
    """Accept member invitation token and create membership assignment."""
    membership = tenancy_repository.accept_invitation(token=request.token, user_id=user.id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired invitation token")
    return membership.to_dict()


# --- SSO Identity Provider APIs ---
@router.get("/organizations/{org_id}/sso", summary="Get organization SSO provider")
async def get_org_sso(org_id: str, user: User = Depends(current_user)):
    """Retrieve SSO identity provider configuration."""
    sso = tenancy_repository.get_sso_provider(org_id=org_id)
    if not sso:
        return {"has_sso": False, "message": "No SSO provider configured for organization."}
    res = sso.to_dict()
    res["has_sso"] = True
    return res


@router.post("/organizations/{org_id}/sso", summary="Configure organization SSO provider")
async def setup_org_sso(org_id: str, request: ConfigureSSORequest, user: User = Depends(current_user)):
    """Configure enterprise OIDC/SAML/Okta/Azure AD SSO provider."""
    sso = tenancy_engine.setup_sso(
        org_id=org_id,
        provider_type=request.provider_type,
        issuer_url=request.issuer_url,
        client_id=request.client_id,
        actor_id=user.id,
    )
    return sso.to_dict()


# --- User Profile Directory APIs ---
@router.get("/users/me/profile", summary="Get current user profile")
async def get_my_profile(user: User = Depends(current_user)):
    """Retrieve user directory profile and preferences."""
    prof = tenancy_repository.get_or_create_profile(user_id=user.id)
    result = prof.to_dict()
    if not result.get("display_name"):
        result["display_name"] = user.name
    return result


@router.put("/users/me/profile", summary="Update user profile")
async def update_my_profile(request: UpdateProfileRequest, user: User = Depends(current_user)):
    """Update user directory profile preferences."""
    prof = tenancy_repository.update_profile(
        user_id=user.id,
        display_name=request.display_name or user.name,
        avatar_url=request.avatar_url,
        timezone=request.timezone,
        language=request.language,
    )
    return prof.to_dict()
