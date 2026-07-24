"""Authentication endpoints."""

from fastapi import APIRouter, Depends
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

    user = await auth_service.register(
        db=db,
        name=request.name,
        email=request.email,
        password=request.password,
    )

    return auth_service.token_pair(user)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:

    user = await auth_service.login(
        db=db,
        email=request.email,
        password=request.password,
    )

    return auth_service.token_pair(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:

    return await auth_service.refresh(
        db=db,
        refresh_token=request.refresh_token,
    )


@router.post(
    "/logout",
    status_code=204,
)
async def logout(
    request: RefreshRequest,
) -> None:

    await auth_service.logout(
        request.refresh_token,
    )


@router.get("/me")
async def me(
    user: User = Depends(current_user),
) -> dict[str, str]:

    return {
        "user_id": str(user.id),
        "name": user.name,
        "email": user.email,
    }