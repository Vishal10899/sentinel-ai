"""Authentication service backed by PostgreSQL."""

import asyncio
import base64
import hashlib
import hmac
import json
import secrets
from typing import Any, Optional, Dict  # <--- Make sure 'Any' is imported here
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
    password: str | bytes,
    salt: str | bytes | None = None,
) -> tuple[str, str]:
    if isinstance(password, bytes):
        password = password.decode("utf-8", errors="replace")
    if isinstance(salt, bytes):
        salt = salt.decode("utf-8", errors="replace")

    salt = salt or secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
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
        from app.rbac import role_repository
        from app.tenancy.models import WorkspaceTenant
        from app.tenancy.repository import tenancy_repository

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

        # Check for pending invitation for this email
        inv = tenancy_repository.get_pending_invitation(email)

        is_bootstrap_admin = settings.is_super_admin_email(email)
        is_first_org_user = False
        org_id = None
        ws_id = None

        if inv:
            # CASE B: Joining via invitation
            org_id = inv.org_id
            ws_id = inv.workspace_id
            target_role_id = inv.role_id
        elif is_bootstrap_admin:
            # CASE D: Bootstrap platform administrator
            org_id = "org-default"
            ws_id = "default"
            target_role_id = "role-super-admin"
        else:
            # CASE A: First user creating a new organization
            # They become Organization Owner and Organization Admin
            is_first_org_user = True
            target_role_id = "role-org-admin"

        user_id = secrets.token_hex(16)
        user = User(
            id=user_id,
            name=name.strip(),
            email=email,
            salt=salt,
            password_hash=password_hash,
        )

        created_org_id = None
        created_ws_id = None
        created_mem_id = None

        try:
            db.add(user)

            if is_first_org_user:
                # 1. Create Organization
                domain = email.split("@")[-1] if "@" in email else "sentinel.ai"
                clean_name = name.strip() or "Enterprise"
                org_slug = (
                    clean_name.lower().replace(" ", "-")
                    + "-org-"
                    + secrets.token_hex(3)
                )
                org = tenancy_repository.create_organization(
                    name=f"{clean_name}'s Org",
                    slug=org_slug,
                    domain=domain,
                    owner_id=user.id,
                )
                created_org_id = org.id
                org_id = org.id

                # 2. Create Workspace
                ws = await workspace_service.create_default_workspace(
                    db=db,
                    owner_id=user.id,
                    owner_name=user.name,
                    commit=False,
                )
                created_ws_id = ws.id if ws else "default"
                ws_id = created_ws_id

                # Register workspace in tenancy repo
                tenancy_repository.register_workspace(
                    WorkspaceTenant(
                        id=ws_id,
                        org_id=org_id,
                        name=ws.name if ws else f"{user.name}'s Workspace",
                        slug=ws.slug if ws else "main",
                        description="Primary tenant workspace",
                        owner_id=user.id,
                    )
                )

                # 3. Create Membership
                mem = tenancy_repository.create_membership(
                    org_id=org_id,
                    workspace_id=ws_id,
                    user_id=user.id,
                    role_id=target_role_id,
                    status="ACTIVE",
                )
                created_mem_id = mem.id

                # 4. Assign Role
                role_repository.assign_user_role(user.id, target_role_id)

            elif inv:
                # Attached to invited org and workspace
                mem = tenancy_repository.create_membership(
                    org_id=org_id,
                    workspace_id=ws_id,
                    user_id=user.id,
                    role_id=target_role_id,
                    status="ACTIVE",
                )
                created_mem_id = mem.id
                inv.status = "ACCEPTED"
                role_repository.assign_user_role(user.id, target_role_id)

            else:
                # Bootstrap admin
                ws = await workspace_service.create_default_workspace(
                    db=db,
                    owner_id=user.id,
                    owner_name=user.name,
                    commit=False,
                )
                ws_id = ws.id if ws else "default"
                mem = tenancy_repository.create_membership(
                    org_id="org-default",
                    workspace_id=ws_id,
                    user_id=user.id,
                    role_id=target_role_id,
                    status="ACTIVE",
                )
                created_mem_id = mem.id
                role_repository.assign_user_role(user.id, target_role_id)

            # Atomic commit
            await db.commit()
            return user

        except Exception as e:
            await db.rollback()
            # Clean up in-memory tenancy/role repository on rollback
            if created_org_id:
                tenancy_repository.delete_organization(created_org_id)
            if created_ws_id:
                tenancy_repository.delete_workspace(created_ws_id)
            if created_mem_id:
                tenancy_repository.delete_membership(created_mem_id)
            tenancy_repository.delete_user_memberships(user_id)
            role_repository.remove_user_role(user_id)
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration transaction failed: {str(e)}",
            ) from e

    async def register_new_user(
        self,
        db: AsyncSession,
        payload: Any,
    ) -> User:
        if hasattr(payload, "email"):
            name = getattr(payload, "name", "")
            email = getattr(payload, "email", "")
            password = getattr(payload, "password", "")
            role = getattr(payload, "role", None)
        elif isinstance(payload, dict):
            name = payload.get("name", "")
            email = payload.get("email", "")
            password = payload.get("password", "")
            role = payload.get("role", None)
        else:
            raise ValueError("Invalid registration payload")
        return await self.register(
            db=db,
            name=name,
            email=email,
            password=password,
            role=role,
        )

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
        if settings.is_super_admin_email(email):
            role_repository.assign_user_role(user.id, "role-super-admin")

        return user

    def get_user_context(self, user: User) -> dict[str, object]:
        from app.rbac import rbac_engine, role_repository
        from app.tenancy.repository import tenancy_repository

        if user.email and settings.is_super_admin_email(user.email):
            role_repository.assign_user_role(user.id, "role-super-admin")

        user_mem = tenancy_repository.get_user_membership(user.id)
        if not user_mem:
            memberships = tenancy_repository.list_members(org_id=None)
            user_mem = next((m for m in memberships if m.user_id == user.id), None)

        if user_mem and user_mem.role_id:
            role_repository.assign_user_role(user.id, user_mem.role_id)

        role = role_repository.get_user_role(user.id)
        effective_permissions = rbac_engine.get_user_effective_permissions(user.id)

        org_id = user_mem.org_id if user_mem else "org-default"
        workspace_id = user_mem.workspace_id if user_mem else "default"

        org = tenancy_repository.get_organization(org_id)
        ws = tenancy_repository.get_workspace(workspace_id)

        is_owner = bool((org and org.owner_id == user.id) or (ws and ws.owner_id == user.id) or (role.id == "role-super-admin"))

        user_title = None
        if user.email and user.email.lower() == settings.bootstrap_super_admin_email_2.lower():
            user_title = settings.bootstrap_super_admin_title_2

        return {
            "user": {
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "role": role.id,
                "role_name": role.name,
                "is_owner": is_owner,
                "title": user_title,
                "permissions": list(effective_permissions),
                "effective_permissions": list(effective_permissions),
            },
            "organization": {
                "id": org.id if org else "org-default",
                "name": org.name if org else "Sentinel Enterprise",
                "slug": org.slug if org else "sentinel-enterprise",
                "domain": org.domain if org else "sentinel.ai",
                "owner_id": org.owner_id if org else "admin",
                "is_owner": bool(org and org.owner_id == user.id),
            },
            "workspace": {
                "id": ws.id if ws else "default",
                "name": ws.name if ws else "Default Production Workspace",
                "slug": ws.slug if ws else "default",
                "owner_id": ws.owner_id if ws else "admin",
            },
            "membership": {
                "id": user_mem.id,
                "org_id": org_id,
                "workspace_id": workspace_id,
                "user_id": user.id,
                "role_id": role.id,
                "status": user_mem.status,
            } if user_mem else None,
            "role": {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "is_builtin": role.is_builtin,
            },
            "permissions": list(effective_permissions),
            "effective_permissions": list(effective_permissions),
            "is_owner": is_owner,
            "title": user_title,
        }


    def _token(
        self,
        user: User,
        token_type: str,
        lifetime: timedelta,
    ) -> str:
        from app.rbac import role_repository

        role_obj = role_repository.get_user_role(user.id)
        role_id = role_obj.id if role_obj else "role-developer"
        if user.email and settings.is_super_admin_email(user.email):
            role_id = "role-super-admin"

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
                "role": role_id,
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

            if "role" in claims and claims["role"]:
                from app.rbac import role_repository
                if not role_repository.has_user_role(user.id):
                    role_repository.assign_user_role(user.id, claims["role"])

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
