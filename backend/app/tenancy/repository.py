import secrets
from uuid import uuid4
from typing import Any

from app.tenancy.models import IdentityProvider, Invitation, Membership, Organization, UserProfile, WorkspaceTenant


class TenancyRepository:
    """Repository managing Organizations, Workspaces, Memberships, Invitations, SSO, and User Profiles."""

    def __init__(self) -> None:
        self._orgs: dict[str, Organization] = {}
        self._workspaces: dict[str, WorkspaceTenant] = {}
        self._memberships: dict[str, Membership] = {}
        self._invitations: dict[str, Invitation] = {}
        self._sso_providers: dict[str, IdentityProvider] = {}
        self._profiles: dict[str, UserProfile] = {}

        self._seed_default_tenant()

    def _seed_default_tenant(self) -> None:
        """Seed default organization & workspace."""
        default_org = Organization(
            id="org-default",
            name="Sentinel Enterprise",
            slug="sentinel-enterprise",
            domain="sentinel.ai",
            owner_id="admin",
        )
        self._orgs[default_org.id] = default_org

        default_ws = WorkspaceTenant(
            id="default",
            org_id="org-default",
            name="Default Production Workspace",
            slug="default",
            description="Primary production workspace",
            owner_id="admin",
        )
        self._workspaces[default_ws.id] = default_ws

    def create_organization(self, name: str, slug: str, domain: str, owner_id: str) -> Organization:
        org_id = f"org-{str(uuid4())[:8]}"
        org = Organization(id=org_id, name=name, slug=slug, domain=domain, owner_id=owner_id)
        self._orgs[org_id] = org

        # Auto-create default workspace for org
        ws_id = f"ws-{str(uuid4())[:8]}"
        ws = WorkspaceTenant(id=ws_id, org_id=org_id, name=f"{name} Main Workspace", slug="main", description="Primary workspace", owner_id=owner_id)
        self._workspaces[ws_id] = ws

        return org

    def list_organizations(self) -> list[Organization]:
        return list(self._orgs.values())

    def get_organization(self, org_id: str) -> Organization | None:
        return self._orgs.get(org_id)

    def create_workspace(self, org_id: str, name: str, slug: str, description: str, owner_id: str) -> WorkspaceTenant:
        ws_id = f"ws-{str(uuid4())[:8]}"
        ws = WorkspaceTenant(id=ws_id, org_id=org_id, name=name, slug=slug, description=description, owner_id=owner_id)
        self._workspaces[ws_id] = ws
        return ws

    def list_workspaces(self, org_id: str | None = None) -> list[WorkspaceTenant]:
        workspaces = list(self._workspaces.values())
        if org_id:
            workspaces = [w for w in workspaces if w.org_id == org_id]
        return workspaces

    def get_workspace(self, workspace_id: str) -> WorkspaceTenant | None:
        return self._workspaces.get(workspace_id)

    def create_invitation(self, org_id: str, workspace_id: str, email: str, role_id: str = "role-developer") -> Invitation:
        inv_id = f"inv-{str(uuid4())[:8]}"
        token = secrets.token_urlsafe(16)
        inv = Invitation(id=inv_id, org_id=org_id, workspace_id=workspace_id, email=email, role_id=role_id, token=token)
        self._invitations[inv_id] = inv
        return inv

    def create_membership(
        self,
        org_id: str,
        workspace_id: str,
        user_id: str,
        role_id: str = "role-developer",
        status: str = "ACTIVE",
    ) -> Membership:
        mem_id = f"mem-{str(uuid4())[:8]}"
        membership = Membership(
            id=mem_id,
            org_id=org_id,
            workspace_id=workspace_id,
            user_id=user_id,
            role_id=role_id,
            status=status,
        )
        self._memberships[mem_id] = membership
        return membership

    def accept_invitation(self, token: str, user_id: str) -> Membership | None:
        inv = next((i for i in self._invitations.values() if i.token == token and i.status == "PENDING"), None)
        if not inv:
            return None

        inv.status = "ACCEPTED"
        mem_id = f"mem-{str(uuid4())[:8]}"
        membership = Membership(id=mem_id, org_id=inv.org_id, workspace_id=inv.workspace_id, user_id=user_id, role_id=inv.role_id)
        self._memberships[mem_id] = membership
        return membership

    def list_members(self, org_id: str | None = None) -> list[Membership]:
        mems = list(self._memberships.values())
        if org_id:
            mems = [m for m in mems if m.org_id == org_id]
        return mems

    def get_pending_invitation(self, email: str) -> Invitation | None:
        """Find pending invitation by email."""
        clean_email = email.strip().lower()
        return next(
            (i for i in self._invitations.values() if i.email.strip().lower() == clean_email and i.status == "PENDING"),
            None,
        )

    def delete_organization(self, org_id: str) -> bool:
        """Delete organization and attached workspaces/memberships (for rollback/cleanup)."""
        if org_id in self._orgs:
            del self._orgs[org_id]
            self._workspaces = {k: v for k, v in self._workspaces.items() if v.org_id != org_id}
            self._memberships = {k: v for k, v in self._memberships.items() if v.org_id != org_id}
            return True
        return False

    def delete_workspace(self, workspace_id: str) -> bool:
        """Delete workspace by ID."""
        if workspace_id in self._workspaces:
            del self._workspaces[workspace_id]
            self._memberships = {k: v for k, v in self._memberships.items() if v.workspace_id != workspace_id}
            return True
        return False

    def delete_membership(self, mem_id: str) -> bool:
        """Delete membership by ID."""
        if mem_id in self._memberships:
            del self._memberships[mem_id]
            return True
        return False

    def delete_user_memberships(self, user_id: str) -> None:
        """Delete all memberships for a user (for rollback)."""
        self._memberships = {k: v for k, v in self._memberships.items() if v.user_id != user_id}

    def get_user_membership(self, user_id: str, org_id: str | None = None) -> Membership | None:
        """Get primary or org-scoped membership for a user."""
        for m in self._memberships.values():
            if m.user_id == user_id:
                if org_id is None or m.org_id == org_id:
                    return m
        return None

    def list_user_organizations(self, user_id: str) -> list[Organization]:
        """List organizations the user owns or is a member of."""
        owned_org_ids = {o.id for o in self._orgs.values() if o.owner_id == user_id}
        member_org_ids = {m.org_id for m in self._memberships.values() if m.user_id == user_id}
        all_org_ids = owned_org_ids.union(member_org_ids)
        return [o for o in self._orgs.values() if o.id in all_org_ids]

    def list_user_workspaces(self, user_id: str) -> list[WorkspaceTenant]:
        """List workspaces the user owns or is a member of."""
        user_orgs = {o.id for o in self.list_user_organizations(user_id)}
        owned_ws = [w for w in self._workspaces.values() if w.owner_id == user_id]
        member_ws = [w for w in self._workspaces.values() if w.org_id in user_orgs]
        seen = set()
        result = []
        for w in owned_ws + member_ws:
            if w.id not in seen:
                seen.add(w.id)
                result.append(w)
        return result

    def register_workspace(self, ws: WorkspaceTenant) -> None:
        """Register or update a workspace instance."""
        self._workspaces[ws.id] = ws

    def configure_sso_provider(self, org_id: str, provider_type: str, issuer_url: str, client_id: str) -> IdentityProvider:
        sso_id = f"sso-{str(uuid4())[:8]}"
        provider = IdentityProvider(id=sso_id, org_id=org_id, provider_type=provider_type, issuer_url=issuer_url, client_id=client_id)
        self._sso_providers[sso_id] = provider
        return provider

    def get_sso_provider(self, org_id: str) -> IdentityProvider | None:
        return next((s for s in self._sso_providers.values() if s.org_id == org_id and s.is_active), None)

    def get_or_create_profile(self, user_id: str, display_name: str = "Sentinel User") -> UserProfile:
        if user_id not in self._profiles:
            self._profiles[user_id] = UserProfile(user_id=user_id, display_name=display_name)
        return self._profiles[user_id]

    def update_profile(self, user_id: str, display_name: str | None = None, avatar_url: str | None = None, timezone: str | None = None, language: str | None = None) -> UserProfile:
        prof = self.get_or_create_profile(user_id)
        if display_name:
            prof.display_name = display_name
        if avatar_url:
            prof.avatar_url = avatar_url
        if timezone:
            prof.timezone = timezone
        if language:
            prof.language = language
        return prof


tenancy_repository = TenancyRepository()
