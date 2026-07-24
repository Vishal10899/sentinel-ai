"""Shared HTTP dependencies."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import auth_service
from app.db.session import get_db
from app.models.user import User

security = HTTPBearer()


async def current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(security),
    ],
    db: AsyncSession = Depends(get_db),
) -> User:

    return await auth_service.user_from_token(
        db=db,
        token=credentials.credentials,
    )