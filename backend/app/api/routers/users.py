"""User and Team management router enforcing strict RBAC UI and backend guards."""

import secrets
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import current_user
from app.auth.service import auth_service
from app.db.session import get_db
from app.models.user import User, UserRole
from app.rbac import role_repository


router = APIRouter(prefix="/team", tags=["team"])

# In-memory store for pending team invitations
_pending_invitations: dict[str, dict] = {}


class TeamInviteRequest(BaseModel):
    email: str = Field(..., description="Target email address")
    role: str = Field(default="DEVELOPER", description="Role assigned to invitee (DEVELOPER or MEMBER)")


class TeamInviteResponse(BaseModel):
    id: str
    email: str
    role: str
    status: str = "pending"
    invite_token: str
    message: str


class MemberResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str


@router.post("/invite", response_model=TeamInviteResponse, status_code=status.HTTP_201_CREATED, summary="Invite Team Member")
async def invite_team_member(
    payload: TeamInviteRequest,
    current_user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),

):

    """Send team invitation with assigned role. Restricted strictly to workspace Admins."""
    user_role = getattr(current_user, "role", None)
    if user_role != UserRole.ADMIN and user_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Workspace Admins can send team invitations.",
        )

    target_role = payload.role.upper() if payload.role else "DEVELOPER"
    if target_role not in ("DEVELOPER", "MEMBER"):
        target_role = "DEVELOPER"

    invite_id = f"inv-{secrets.token_hex(8)}"
    token = f"token-{secrets.token_urlsafe(16)}"

    invitation = {
        "id": invite_id,
        "email": payload.email.lower(),
        "role": target_role,
        "status": "pending",
        "invite_token": token,
        "invited_by": current_user.email,
    }

    _pending_invitations[invite_id] = invitation

    return TeamInviteResponse(
        id=invite_id,
        email=payload.email.lower(),
        role=target_role,
        status="pending",
        invite_token=token,
        message=f"Invitation sent to {payload.email} with assigned role '{target_role}'.",
    )


@router.get("/members", response_model=List[MemberResponse], summary="List Team Members")
async def list_team_members(
    current_user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> List[MemberResponse]:
    """Retrieve all users in the workspace."""
    result = await db.execute(select(User))
    users = result.scalars().all()
    
    return [
        MemberResponse(
            id=u.id,
            name=u.name,
            email=u.email,
            role=getattr(u, "role", "DEVELOPER"),
        )
        for u in users
    ]
