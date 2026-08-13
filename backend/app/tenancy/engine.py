from typing import Any

from app.audit.engine import audit_engine
from app.tenancy.models import IdentityProvider, Invitation, Membership, Organization, UserProfile, WorkspaceTenant
from app.tenancy.repository import TenancyRepository, tenancy_repository


class TenancyEngine:
    """Enterprise Multi-Tenant Isolation & Identity Engine."""

    def __init__(self, repository: TenancyRepository | None = None) -> None:
        self.repository = repository or tenancy_repository

    def create_organization(self, name: str, slug: str, domain: str, owner_id: str) -> Organization:
        """Create new organization and emit audit event."""
        org = self.repository.create_organization(name=name, slug=slug, domain=domain, owner_id=owner_id)
        audit_engine.record_event(
            action="ORGANIZATION_CREATED",
            resource=f"organizations/{org.id}",
            user_id=owner_id,
            workspace_id="default",
            new_value=f"Org: {org.name} ({org.slug})",
        )
        return org

    def create_workspace(self, org_id: str, name: str, slug: str, description: str, owner_id: str) -> WorkspaceTenant:
        """Create new workspace tenant and emit audit event."""
        ws = self.repository.create_workspace(org_id=org_id, name=name, slug=slug, description=description, owner_id=owner_id)
        audit_engine.record_event(
            action="WORKSPACE_CREATED",
            resource=f"workspaces/{ws.id}",
            user_id=owner_id,
            workspace_id=ws.id,
            new_value=f"Workspace: {ws.name}",
        )
        return ws

    def invite_member(self, org_id: str, workspace_id: str, email: str, role_id: str, inviter_user_id: str) -> Invitation:
        """Issue member invitation token and emit audit event."""
        inv = self.repository.create_invitation(org_id=org_id, workspace_id=workspace_id, email=email, role_id=role_id)
        audit_engine.record_event(
            action="MEMBER_INVITED",
            resource=f"invitations/{inv.id}",
            user_id=inviter_user_id,
            workspace_id=workspace_id,
            new_value=f"Invited: {email}",
        )
        return inv

    def setup_sso(self, org_id: str, provider_type: str, issuer_url: str, client_id: str, actor_id: str) -> IdentityProvider:
        """Configure enterprise SSO identity provider and emit audit event."""
        sso = self.repository.configure_sso_provider(org_id=org_id, provider_type=provider_type, issuer_url=issuer_url, client_id=client_id)
        audit_engine.record_event(
            action="IDENTITY_PROVIDER_UPDATED",
            resource=f"sso/{sso.id}",
            user_id=actor_id,
            workspace_id="default",
            new_value=f"SSO Provider: {provider_type} ({issuer_url})",
        )
        return sso


tenancy_engine = TenancyEngine()
