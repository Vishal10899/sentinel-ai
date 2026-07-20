"""Shared HTTP dependencies."""
from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.auth.service import User, auth_service

security = HTTPBearer()
async def current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> User:
    return auth_service.user_from_token(credentials.credentials)
