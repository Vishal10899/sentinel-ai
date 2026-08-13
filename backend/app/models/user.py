from enum import Enum
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"
    MEMBER = "MEMBER"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    salt: Mapped[str] = mapped_column(String(64), nullable=False)

    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def role(self) -> str:
        """Resolve user role dynamically via RBAC role_repository / bootstrap admin."""
        from app.core.settings import settings
        from app.rbac.repository import role_repository

        if self.email and self.email.lower() == settings.bootstrap_admin_email.lower():
            return UserRole.ADMIN.value

        role_obj = role_repository.get_user_role(self.id)
        if role_obj.id in ("role-super-admin", "role-org-admin", "role-workspace-admin", "role-platform-admin"):
            return UserRole.ADMIN.value
        elif role_obj.id in ("role-developer", "role-ai-engineer"):
            return UserRole.DEVELOPER.value
        elif role_obj.id in ("role-viewer", "role-analyst", "role-service-account"):
            return UserRole.MEMBER.value

        return UserRole.DEVELOPER.value

    @role.setter
    def role(self, value: str) -> None:
        """Update role assignment in RBAC repository if set explicitly on instance."""
        from app.rbac.repository import role_repository

        role_map = {
            "ADMIN": "role-super-admin",
            "DEVELOPER": "role-developer",
            "MEMBER": "role-viewer",
        }
        role_id = role_map.get(str(value).upper(), "role-developer")
        if self.id:
            role_repository.assign_user_role(self.id, role_id)

    @property
    def workspace_id(self) -> str | None:
        """Resolve primary workspace_id from tenancy memberships."""
        from app.tenancy.repository import tenancy_repository

        mems = tenancy_repository.list_members(org_id=None)
        user_mem = next((m for m in mems if m.user_id == self.id), None)
        return user_mem.workspace_id if user_mem else "default"

    @workspace_id.setter
    def workspace_id(self, value: str | None) -> None:
        pass