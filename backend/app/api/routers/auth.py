"""Authentication endpoints."""
from fastapi import APIRouter, Depends
from app.api.dependencies import current_user
from app.api.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.auth.service import User, auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest) -> dict[str, object]: return auth_service.token_pair(auth_service.register(request.name, request.email, request.password))
@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> dict[str, object]: return auth_service.token_pair(auth_service.login(request.email, request.password))
@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest) -> dict[str, object]: return auth_service.refresh(request.refresh_token)
@router.post("/logout", status_code=204)
async def logout(request: RefreshRequest) -> None: auth_service.logout(request.refresh_token)
@router.get("/me")
async def me(user: User = Depends(current_user)) -> dict[str, str]: return user.public()
