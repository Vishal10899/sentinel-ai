from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import auth_service
from app.db.session import get_db
from app.models.user import User
from app.rbac import rbac_engine

security = HTTPBearer(auto_error=False)


async def current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security),
    ],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate Bearer JWT token strictly and return authenticated User."""
    if credentials and credentials.credentials:
        try:
            return await auth_service.user_from_token(
                db=db,
                token=credentials.credentials,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication credentials were not provided",
    )


def require_permission(permission: str):
    """Server-side authorization enforcement verifying user has required permission."""
    async def _permission_dependency(user: User = Depends(current_user)) -> User:
        allowed = rbac_engine.check_permission(user.id, permission)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Required permission '{permission}' is missing for this account.",
            )
        return user
    return _permission_dependency