from fastapi import HTTPException, Request, status

from app.security.keys import VirtualKey
from app.security.repository import VirtualKeyRepository, virtual_key_repository


class VirtualKeyAuthenticator:
    """Validates incoming Virtual API Keys from request headers and enforces key-level permissions."""

    def __init__(self, repository: VirtualKeyRepository | None = None) -> None:
        self.repository = repository or virtual_key_repository

    def extract_key_from_request(self, request: Request) -> str | None:
        """Extract key secret from X-Sentinel-API-Key or Bearer token header."""
        # 1. Custom Header
        header_key = request.headers.get("X-Sentinel-API-Key")
        if header_key:
            return header_key.strip()

        # 2. Authorization Header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
            if token.startswith("sk-snt-"):
                return token
        return None

    def authenticate_request(self, request: Request, provider_id: str | None = None, model_id: str | None = None) -> VirtualKey | None:
        """Validate virtual key, checking expiration, provider restrictions, and model permissions."""
        secret = self.extract_key_from_request(request)
        if not secret:
            return None  # Fallback to session / default auth

        vk = self.repository.authenticate_secret(secret)
        if not vk:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, expired, or revoked Virtual API Key.",
            )

        # Check allowed providers restriction
        if provider_id and vk.allowed_providers:
            if provider_id not in vk.allowed_providers:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Virtual Key '{vk.name}' is not authorized to access provider '{provider_id}'.",
                )

        # Check allowed models restriction
        if model_id and vk.allowed_models:
            if model_id not in vk.allowed_models:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Virtual Key '{vk.name}' is not authorized to access model '{model_id}'.",
                )

        return vk


key_authenticator = VirtualKeyAuthenticator()
