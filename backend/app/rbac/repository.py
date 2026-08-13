"""Repository managing built-in roles, custom roles, and user role assignments."""

from typing import Any
from uuid import uuid4

from app.rbac.models import ALL_PERMISSIONS, Role


class RoleRepository:
    """Repository managing built-in roles, custom roles, and user role assignments."""

    def __init__(self) -> None:
        self._roles: dict[str, Role] = {}
        self._user_roles: dict[str, str] = {}  # user_id -> role_id

        self._seed_builtin_roles()

    def _seed_builtin_roles(self) -> None:
        """Seed standard enterprise built-in roles as per Sprint 3.0 specs."""
        builtin_roles = [
            Role(
                id="role-super-admin",
                name="Super Admin",
                description="Unconstrained global root access across all tenants, workspaces, and system settings.",
                permissions=["*"],
                is_builtin=True,
            ),
            Role(
                id="role-org-admin",
                name="Organization Admin",
                description="Administrative authority over organization workspaces, users, policies, and billing.",
                permissions=[
                    "view_models", "manage_providers", "create_api_keys", "delete_conversations",
                    "manage_policies", "view_analytics", "export_data", "manage_users",
                    "manage_workspaces", "manage_billing", "chat.read", "chat.write", "chat.delete",
                    "conversation.read", "conversation.delete", "provider.manage", "model.manage",
                    "policy.manage", "cache.manage", "guardrails.manage", "apikey.manage",
                    "workspace.manage", "analytics.read", "audit.read", "audit.export",
                    "billing.manage", "settings.manage", "users.manage", "roles.manage",
                ],
                inherits_from=["role-workspace-admin"],
                is_builtin=True,
            ),
            Role(
                id="role-workspace-admin",
                name="Workspace Admin",
                description="Full control over workspace settings, API keys, policies, and members.",
                permissions=[
                    "view_models", "create_api_keys", "delete_conversations", "manage_policies",
                    "view_analytics", "export_data", "manage_workspaces", "chat.read", "chat.write",
                    "chat.delete", "conversation.read", "conversation.delete", "policy.manage",
                    "cache.manage", "guardrails.manage", "apikey.manage", "workspace.manage", "analytics.read",
                ],
                inherits_from=["role-ai-engineer"],
                is_builtin=True,
            ),
            Role(
                id="role-ai-engineer",
                name="AI Engineer",
                description="Prompt engineering, model routing management, cache tuning, and telemetry inspection.",
                permissions=[
                    "view_models", "manage_providers", "provider.manage", "model.manage",
                    "cache.manage", "guardrails.manage", "view_analytics",
                    "export_data", "chat.read", "chat.write", "conversation.read", "analytics.read",
                ],
                inherits_from=["role-developer"],
                is_builtin=True,
            ),
            Role(
                id="role-analyst",
                name="Analyst",
                description="Access to conversation history, cost analytics, and security audit logs.",
                permissions=["view_models", "view_analytics", "export_data", "chat.read", "conversation.read", "analytics.read", "audit.read"],
                inherits_from=["role-viewer"],
                is_builtin=True,
            ),
            Role(
                id="role-developer",
                name="Developer",
                description="Access to chat playground, conversation history, and cache stats.",
                permissions=["view_models", "chat.read", "chat.write", "conversation.read", "conversation.delete", "analytics.read"],
                inherits_from=["role-viewer"],
                is_builtin=True,
            ),
            Role(
                id="role-viewer",
                name="Viewer",
                description="Read-only inspection access to conversation history and model catalog.",
                permissions=["view_models", "chat.read", "conversation.read"],
                is_builtin=True,
            ),
            Role(
                id="role-service-account",
                name="Service Account",
                description="Non-human programmatic API execution role.",
                permissions=["view_models", "chat.read", "chat.write", "conversation.read"],
                is_builtin=True,
            ),
            # Maintain backward compatibility alias
            Role(
                id="role-platform-admin",
                name="Platform Admin",
                description="Platform Admin alias for Super Admin.",
                permissions=["*"],
                is_builtin=True,
            ),
        ]

        for role in builtin_roles:
            self._roles[role.id] = role

    def list_roles(self) -> list[Role]:
        """List all available roles."""
        return list(self._roles.values())

    def get_role(self, role_id: str) -> Role | None:
        """Retrieve role by ID or alias."""
        if role_id in self._roles:
            return self._roles[role_id]
        # Search by name match
        for r in self._roles.values():
            if r.name.lower() == role_id.lower().replace("_", " "):
                return r
        return None

    def get_effective_permissions(self, role_id: str) -> set[str]:
        """Resolve role permissions including inheritance graph."""
        role = self.get_role(role_id)
        if not role:
            return set()
        if "*" in role.permissions:
            return set(ALL_PERMISSIONS).union({"*"})

        effective = set(role.permissions)
        visited = {role_id}
        queue = list(role.inherits_from)

        while queue:
            parent_id = queue.pop(0)
            if parent_id in visited:
                continue
            visited.add(parent_id)
            parent_role = self.get_role(parent_id)
            if parent_role:
                effective.update(parent_role.permissions)
                queue.extend([p for p in parent_role.inherits_from if p not in visited])

        return effective

    def create_role(self, name: str, description: str, permissions: list[str]) -> Role:
        """Create a custom role."""
        role_id = f"custom-{uuid4().hex[:8]}"
        role = Role(
            id=role_id,
            name=name,
            description=description,
            permissions=permissions,
            is_builtin=False,
        )
        self._roles[role.id] = role
        return role

    def update_role(self, role_id: str, name: str | None = None, description: str | None = None, permissions: list[str] | None = None) -> Role | None:
        """Update a custom role. Built-in roles cannot be updated."""
        role = self.get_role(role_id)
        if not role or role.is_builtin:
            return None
        if name:
            role.name = name
        if description is not None:
            role.description = description
        if permissions is not None:
            role.permissions = permissions
        return role

    def delete_role(self, role_id: str) -> bool:
        """Delete a custom role. Built-in roles cannot be deleted."""
        role = self.get_role(role_id)
        if not role or role.is_builtin:
            return False
        del self._roles[role_id]
        return True

    def assign_user_role(self, user_id: str, role_id: str) -> bool:
        """Assign a role to a user."""
        role = self.get_role(role_id)
        if not role:
            return False
        self._user_roles[user_id] = role.id
        return True

    def has_user_role(self, user_id: str) -> bool:
        """Check if user has an explicitly assigned role in repository."""
        return user_id in self._user_roles

    def get_user_role(self, user_id: str) -> Role:
        """Get role assigned to a user (defaults to role-super-admin for system admin, role-viewer for others)."""
        if user_id in self._user_roles:
            role_id = self._user_roles[user_id]
        elif user_id in ("admin", "default_user", "system"):
            role_id = "role-super-admin"
        else:
            role_id = "role-viewer"
        return self._roles.get(role_id, self._roles["role-viewer"])


role_repository = RoleRepository()
