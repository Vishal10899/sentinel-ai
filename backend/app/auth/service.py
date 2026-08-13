"""Authentication service backed by PostgreSQL."""

import asyncio
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
        role: str | None = None,
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

        salt, password_hash = await asyncio.to_thread(_hash, password)

        # First-user rule check
        from sqlalchemy import func
        count_res = await db.execute(select(func.count(User.id)))
        user_count = count_res.scalar() or 0

        if email == settings.bootstrap_admin_email.lower() or (user_count == 0 and ("admin" in email or role == "ADMIN")):
            assigned_role = "ADMIN"
            target_role_id = "role-super-admin"
        elif role == "MEMBER":
            assigned_role = "MEMBER"
            target_role_id = "role-viewer"
        else:
            assigned_role = "DEVELOPER"
            target_role_id = "role-developer"

        user = User(
            id=secrets.token_hex(16),
            name=name.strip(),
            email=email,
            salt=salt,
            password_hash=password_hash,
            role=assigned_role,
        )

        db.add(user)

        await db.commit()

        await workspace_service.create_default_workspace(
            db=db,
            owner_id=user.id,
            owner_name=user.name,
        )

        from app.rbac import role_repository
        role_repository.assign_user_role(user.id, target_role_id)

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

        _, computed_hash = await asyncio.to_thread(_hash, password, user.salt)

        if not hmac.compare_digest(
            computed_hash,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        from app.rbac import role_repository
        if email == settings.bootstrap_admin_email.lower():
            user.role = "ADMIN"
            role_repository.assign_user_role(user.id, "role-super-admin")
        elif getattr(user, "role", None) == "ADMIN":
            role_repository.assign_user_role(user.id, "role-super-admin")
        elif getattr(user, "role", None) == "DEVELOPER":
            role_repository.assign_user_role(user.id, "role-developer")

        return user

    def get_user_context(self, user: User) -> dict[str, object]:
        from app.rbac import rbac_engine, role_repository
        from app.tenancy.repository import tenancy_repository

        if user.email and user.email.lower() == settings.bootstrap_admin_email.lower():
            user.role = "ADMIN"
            role_repository.assign_user_role(user.id, "role-super-admin")

        user_role_val = getattr(user, "role", "DEVELOPER")
        if user_role_val == "ADMIN":
            role_repository.assign_user_role(user.id, "role-super-admin")

        role = role_repository.get_user_role(user.id)
        effective_permissions = rbac_engine.get_user_effective_permissions(user.id)

        memberships = tenancy_repository.list_members(org_id=None)
        user_mem = next((m for m in memberships if m.user_id == user.id), None)

        org_id = user_mem.org_id if user_mem else "org-default"
        workspace_id = user_mem.workspace_id if user_mem else "default"

        org = tenancy_repository.get_organization(org_id)
        ws = tenancy_repository.get_workspace(workspace_id)

        return {
            "user": {
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user_role_val,
            },
            "organization": {
                "id": org.id if org else "org-default",
                "name": org.name if org else "Sentinel Enterprise",
                "slug": org.slug if org else "sentinel-enterprise",
            },
            "workspace": {
                "id": ws.id if ws else "default",
                "name": ws.name if ws else "Default Production Workspace",
                "slug": ws.slug if ws else "default",
            },
            "role": {
                "id": role.id,
                "name": role.name,
                "is_builtin": role.is_builtin,
            },
            "permissions": effective_permissions,
        }

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

        context = self.get_user_context(user)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            **context,
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
