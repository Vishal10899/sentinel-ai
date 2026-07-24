"""Authentication service backed by PostgreSQL."""

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.user import User
from app.services.workspace_service import workspace_service


def _encode(value: dict) -> str:
    return (
        base64.urlsafe_b64encode(
            json.dumps(
                value,
                separators=(",", ":"),
            ).encode()
        )
        .rstrip(b"=")
        .decode()
    )


def _decode(value: str) -> dict:
    return json.loads(
        base64.urlsafe_b64decode(
            value + "=" * (-len(value) % 4)
        )
    )


def _hash(
    password: str,
    salt: str | None = None,
) -> tuple[str, str]:

    salt = salt or secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        310_000,
    ).hex()

    return salt, digest


class AuthService:

    async def register(
        self,
        db: AsyncSession,
        name: str,
        email: str,
        password: str,
    ) -> User:

        email = email.strip().lower()

        result = await db.execute(
            select(User).where(User.email == email)
        )

        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account already exists for this email",
            )

        salt, password_hash = _hash(password)

        user = User(
            id=secrets.token_hex(16),
            name=name.strip(),
            email=email,
            salt=salt,
            password_hash=password_hash,
        )

        db.add(user)

        await db.commit()
        await db.refresh(user)

        await workspace_service.create_default_workspace(
            db=db,
            owner_id=user.id,
            owner_name=user.name,
        )

        return user

    async def login(
        self,
        db: AsyncSession,
        email: str,
        password: str,
    ) -> User:

        email = email.strip().lower()

        result = await db.execute(
            select(User).where(User.email == email)
        )

        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not hmac.compare_digest(
            _hash(password, user.salt)[1],
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        return user

    def _token(
        self,
        user: User,
        token_type: str,
        lifetime: timedelta,
    ) -> str:

        now = datetime.now(timezone.utc)

        header = _encode(
            {
                "alg": "HS256",
                "typ": "JWT",
            }
        )

        payload = _encode(
            {
                "sub": user.id,
                "email": user.email,
                "type": token_type,
                "iat": int(now.timestamp()),
                "exp": int((now + lifetime).timestamp()),
            }
        )

        signature = hmac.new(
            settings.jwt_secret.encode(),
            f"{header}.{payload}".encode(),
            hashlib.sha256,
        ).digest()

        signature = (
            base64.urlsafe_b64encode(signature)
            .rstrip(b"=")
            .decode()
        )

        return f"{header}.{payload}.{signature}"

    def token_pair(
        self,
        user: User,
    ) -> dict[str, object]:

        access_token = self._token(
            user=user,
            token_type="access",
            lifetime=timedelta(
                minutes=settings.jwt_access_token_minutes,
            ),
        )

        refresh_token = self._token(
            user=user,
            token_type="refresh",
            lifetime=timedelta(
                days=settings.jwt_refresh_token_days,
            ),
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
            },
        }

    async def user_from_token(
        self,
        db: AsyncSession,
        token: str,
        expected_type: str = "access",
    ) -> User:

        try:
            header, payload, signature = token.split(".")

            expected_signature = hmac.new(
                settings.jwt_secret.encode(),
                f"{header}.{payload}".encode(),
                hashlib.sha256,
            ).digest()

            actual_signature = base64.urlsafe_b64decode(
                signature + "=" * (-len(signature) % 4)
            )
            if not hmac.compare_digest(expected_signature, actual_signature):
                raise ValueError("Invalid token signature")

            claims = _decode(payload)
            if claims["type"] != expected_type:
                raise ValueError("Invalid token type")

            if int(claims["exp"]) < int(
                datetime.now(timezone.utc).timestamp()
            ):
                raise ValueError("Token expired")

            result = await db.execute(
                select(User).where(
                    User.id == str(claims["sub"])
                )
            )

            user = result.scalar_one_or_none()
            if user is None:
                raise ValueError("User not found")

            return user

        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

    async def refresh(
        self,
        db: AsyncSession,
        refresh_token: str,
    ) -> dict[str, object]:

        user = await self.user_from_token(
            db=db,
            token=refresh_token,
            expected_type="refresh",
        )

        return self.token_pair(user)

    async def logout(
        self,
        refresh_token: str,
    ) -> None:
        return None


auth_service = AuthService()
