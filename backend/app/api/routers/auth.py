"""Authentication endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import current_user
from app.api.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.auth.service import auth_service
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=TokenResponse,
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:

    try:
        user = await auth_service.register(
            db=db,
            name=request.name,
            email=request.email,
            password=request.password,
        )
        return auth_service.token_pair(user)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:

    try:
        user = await auth_service.login(
            db=db,
            email=request.email,
            password=request.password,
        )
        return auth_service.token_pair(user)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Login failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:

    try:
        return await auth_service.refresh(
            db=db,
            refresh_token=request.refresh_token,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


@router.post(
    "/logout",
    status_code=204,
)
async def logout(
    request: RefreshRequest,
) -> None:

    try:
        await auth_service.logout(
            request.refresh_token,
        )
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}", exc_info=True)


@router.get("/me")
async def me(
    user: User = Depends(current_user),
) -> dict[str, object]:

    try:
        return auth_service.get_user_context(user)
    except Exception as e:
        logger.error(f"Failed to fetch user context: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user context: {str(e)}",
        )