import time
from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class Organization:
    """Enterprise Multi-Tenant Organization model."""

    id: str
    name: str
    slug: str
    domain: str
    owner_id: str
    logo_url: str = ""
    theme: str = "dark"
    status: str = "ACTIVE"  # ACTIVE, SUSPENDED
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorkspaceTenant:
    """Isolated Tenant Workspace model."""

    id: str
    org_id: str
    name: str
    slug: str
    description: str
    owner_id: str
    is_active: bool = True
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Membership:
    """Organization & Workspace Member Assignment."""

    id: str
    org_id: str
    workspace_id: str
    user_id: str
    role_id: str
    status: str = "ACTIVE"  # ACTIVE, INVITED, SUSPENDED
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Invitation:
    """Member Invitation Token."""

    id: str
    org_id: str
    workspace_id: str
    email: str
    role_id: str
    token: str
    status: str = "PENDING"  # PENDING, ACCEPTED, EXPIRED
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IdentityProvider:
    """Enterprise SSO & Identity Provider Configuration (SAML / OIDC / Okta / Azure AD)."""

    id: str
    org_id: str
    provider_type: str  # SAML, OIDC, OKTA, AZURE_AD, GOOGLE_WORKSPACE
    issuer_url: str
    client_id: str
    metadata_url: str = ""
    is_active: bool = True
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UserProfile:
    """User Directory Profile & Preferences."""

    user_id: str
    display_name: str
    avatar_url: str = ""
    timezone: str = "UTC"
    language: str = "en"
    preferences: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
