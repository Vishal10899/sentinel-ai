"""Enterprise RBAC Domain Models & Granular Permission Definitions."""

from dataclasses import asdict, dataclass, field
from typing import Any

ALL_PERMISSIONS = [
    "view_models",
    "manage_providers",
    "create_api_keys",
    "delete_conversations",
    "manage_policies",
    "view_analytics",
    "export_data",
    "manage_users",
    "manage_workspaces",
    "manage_billing",
    "chat.read",
    "chat.write",
    "chat.delete",
    "conversation.read",
    "conversation.delete",
    "provider.manage",
    "model.manage",
    "policy.manage",
    "cache.manage",
    "guardrails.manage",
    "apikey.manage",
    "workspace.manage",
    "analytics.read",
    "audit.read",
    "audit.export",
    "billing.manage",
    "settings.manage",
    "users.manage",
    "roles.manage",
]


@dataclass
class Role:
    """Enterprise Role model containing granular permission scopes and inheritance."""

    id: str
    name: str
    description: str
    permissions: list[str] = field(default_factory=list)
    inherits_from: list[str] = field(default_factory=list)
    is_builtin: bool = False

    def has_permission(self, permission: str, inherited_perms: set[str] | None = None) -> bool:
        """Check if role or inherited roles grant a specific permission or wildcard access."""
        all_p = set(self.permissions).union(inherited_perms or set())
        if "*" in all_p or "admin" in all_p:
            return True
        return permission in all_p

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
