"use client";

import { useEffect, useState } from "react";
import { Building2, Plus, Users, Shield, KeyRound, Mail, CheckCircle2, Sliders, Globe, RefreshCw } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import { api } from "../../lib/api";

export default function OrganizationsPage() {
  const [orgs, setOrgs] = useState([]);
  const [selectedOrgId, setSelectedOrgId] = useState(null);
  const [workspaces, setWorkspaces] = useState([]);
  const [members, setMembers] = useState([]);
  const [sso, setSso] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  // Modals
  const [showOrgModal, setShowOrgModal] = useState(false);
  const [showWsModal, setShowWsModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);

  // Forms
  const [orgForm, setOrgForm] = useState({ name: "", slug: "", domain: "" });
  const [wsForm, setWsForm] = useState({ name: "", slug: "", description: "" });
  const [inviteForm, setInviteForm] = useState({ email: "", role_id: "role-developer" });
  const [ssoForm, setSsoForm] = useState({ provider_type: "OKTA", issuer_url: "", client_id: "" });

  const loadOrgs = async () => {
    try {
      setLoading(true);
      const data = await api.getOrganizations();
      setOrgs(data || []);
      if (data && data.length > 0 && !selectedOrgId) {
        setSelectedOrgId(data[0].id);
      }
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadOrgDetails = async (orgId) => {
    if (!orgId) return;
    try {
      const [wsData, memData, ssoData] = await Promise.all([
        api.getWorkspaces(orgId),
        api.getOrgMembers(orgId),
        api.getOrgSSO(orgId),
      ]);
      setWorkspaces(wsData || []);
      setMembers(memData || []);
      setSso(ssoData || null);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadOrgs();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      loadOrgDetails(selectedOrgId);
    }
  }, [selectedOrgId]);

  const handleCreateOrg = async (e) => {
    e.preventDefault();
    try {
      const newOrg = await api.createOrganization(orgForm);
      setToast({ type: "success", message: `Organization '${newOrg.name}' created!` });
      setShowOrgModal(false);
      loadOrgs();
    } catch (err) {
      setToast({ type: "error", message: `Failed: ${err.message}` });
    }
  };

  const handleCreateWorkspace = async (e) => {
    e.preventDefault();
    try {
      await api.createWorkspace({ ...wsForm, org_id: selectedOrgId });
      setToast({ type: "success", message: "Workspace created successfully!" });
      setShowWsModal(false);
      loadOrgDetails(selectedOrgId);
    } catch (err) {
      setToast({ type: "error", message: `Failed: ${err.message}` });
    }
  };

  const handleInviteMember = async (e) => {
    e.preventDefault();
    try {
      const res = await api.inviteMember(selectedOrgId, {
        workspace_id: workspaces[0]?.id || "default",
        email: inviteForm.email,
        role_id: inviteForm.role_id,
      });
      setToast({ type: "success", message: `Invitation token created for ${inviteForm.email}` });
      setShowInviteModal(false);
      loadOrgDetails(selectedOrgId);
    } catch (err) {
      setToast({ type: "error", message: `Failed: ${err.message}` });
    }
  };

  const handleSetupSSO = async (e) => {
    e.preventDefault();
    try {
      const res = await api.setupOrgSSO(selectedOrgId, ssoForm);
      setSso(res);
      setToast({ type: "success", message: "SSO Provider configured!" });
    } catch (err) {
      setToast({ type: "error", message: `Failed: ${err.message}` });
    }
  };

  const selectedOrg = orgs.find((o) => o.id === selectedOrgId);

  return (
    <AppShell>
      <div className="space-y-6">
        <PageTitle
          title="Organizations & Multi-Tenant Workspaces"
          subtitle="Manage isolated multi-tenant enterprise organizations, workspaces, member directory, and SAML/OIDC SSO identity providers."
          action={
            <div className="flex gap-2">
              <Button onClick={() => setShowOrgModal(true)}>
                <Building2 className="h-4 w-4" /> Create Organization
              </Button>
            </div>
          }
        />

        {toast && <Toast type={toast.type} message={toast.message} onClose={() => setToast(null)} />}

        {loading ? (
          <LoadingCard title="Loading Organizations..." />
        ) : error ? (
          <ErrorCard title="Organization Load Error" message={error} onRetry={loadOrgs} />
        ) : (
          <>
            {/* Organization Selector Bar */}
            <div className="flex border-b border-white/10 overflow-x-auto gap-4">
              {orgs.map((org) => (
                <button
                  key={org.id}
                  onClick={() => setSelectedOrgId(org.id)}
                  className={`pb-3 transition font-semibold text-xs flex items-center gap-2 border-b-2 shrink-0 ${
                    selectedOrgId === org.id ? "border-indigo-500 text-indigo-400" : "border-transparent text-slate-400 hover:text-white"
                  }`}
                >
                  <Building2 className="h-4 w-4" /> {org.name}
                </button>
              ))}
            </div>

            {selectedOrg && (
              <div className="space-y-6">
                {/* Workspaces Overview */}
                <div className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="text-sm font-bold text-white flex items-center gap-2">
                        <Globe className="h-4 w-4 text-indigo-400" /> Workspaces in {selectedOrg.name}
                      </h3>
                      <p className="text-xs text-slate-400 font-mono">Domain: {selectedOrg.domain}</p>
                    </div>
                    <Button variant="zinc" onClick={() => setShowWsModal(true)}>
                      <Plus className="h-4 w-4" /> New Workspace
                    </Button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {workspaces.map((ws) => (
                      <div key={ws.id} className="rounded-xl border border-white/10 bg-black/40 p-4 space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-white text-xs">{ws.name}</span>
                          <Badge variant="emerald">Isolated</Badge>
                        </div>
                        <p className="text-xs text-slate-400 font-mono text-[11px]">ID: {ws.id}</p>
                        <p className="text-xs text-slate-300">{ws.description}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Member Directory & SSO Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Member Directory */}
                  <div className="lg:col-span-2 surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="text-sm font-bold text-white flex items-center gap-2">
                        <Users className="h-4 w-4 text-indigo-400" /> Organization Members & Directory
                      </h3>
                      <Button variant="zinc" onClick={() => setShowInviteModal(true)}>
                        <Mail className="h-4 w-4" /> Invite Member
                      </Button>
                    </div>

                    <table className="w-full text-left text-xs text-slate-300">
                      <thead className="border-b border-white/10 bg-white/[0.02] uppercase text-[10px] text-slate-400 font-bold">
                        <tr>
                          <th className="p-3">User ID</th>
                          <th className="p-3">Role</th>
                          <th className="p-3">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/10 font-mono text-[11px]">
                        {members.map((m) => (
                          <tr key={m.id}>
                            <td className="p-3 text-white font-semibold">{m.user_id}</td>
                            <td className="p-3 text-indigo-300">{m.role_id}</td>
                            <td className="p-3">
                              <Badge variant={m.status === "ACTIVE" ? "emerald" : "amber"}>{m.status}</Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* SSO Identity Provider Config */}
                  <div className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <KeyRound className="h-4 w-4 text-cyan-400" /> SSO Identity Provider
                    </h3>

                    {sso?.has_sso ? (
                      <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 space-y-2 text-xs">
                        <div className="flex justify-between items-center font-bold text-emerald-300">
                          <span>{sso.provider_type} SSO Active</span>
                          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                        </div>
                        <p className="font-mono text-slate-300 text-[11px]">Issuer: {sso.issuer_url}</p>
                        <p className="font-mono text-slate-300 text-[11px]">Client ID: {sso.client_id}</p>
                      </div>
                    ) : (
                      <form onSubmit={handleSetupSSO} className="space-y-3 text-xs">
                        <div>
                          <label className="font-semibold text-slate-300 block mb-1">Provider Type</label>
                          <select
                            value={ssoForm.provider_type}
                            onChange={(e) => setSsoForm({ ...ssoForm, provider_type: e.target.value })}
                            className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                          >
                            <option value="OKTA">Okta SSO</option>
                            <option value="AZURE_AD">Azure AD</option>
                            <option value="GOOGLE_WORKSPACE">Google Workspace</option>
                            <option value="SAML">Custom SAML 2.0</option>
                            <option value="OIDC">Custom OIDC</option>
                          </select>
                        </div>

                        <div>
                          <label className="font-semibold text-slate-300 block mb-1">Issuer / Metadata URL</label>
                          <input
                            type="url"
                            required
                            value={ssoForm.issuer_url}
                            onChange={(e) => setSsoForm({ ...ssoForm, issuer_url: e.target.value })}
                            placeholder="https://sso.enterprise.com"
                            className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                          />
                        </div>

                        <div>
                          <label className="font-semibold text-slate-300 block mb-1">Client ID</label>
                          <input
                            type="text"
                            required
                            value={ssoForm.client_id}
                            onChange={(e) => setSsoForm({ ...ssoForm, client_id: e.target.value })}
                            placeholder="sso-client-id-123"
                            className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                          />
                        </div>

                        <Button type="submit" className="w-full">Configure SSO</Button>
                      </form>
                    )}
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {/* Modal: Create Organization */}
        {showOrgModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <form onSubmit={handleCreateOrg} className="w-full max-w-md rounded-2xl border border-white/10 bg-[#111827] p-6 shadow-2xl space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Building2 className="h-5 w-5 text-indigo-400" /> Create Enterprise Organization
              </h3>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Organization Name</label>
                <input
                  type="text"
                  required
                  value={orgForm.name}
                  onChange={(e) => setOrgForm({ ...orgForm, name: e.target.value })}
                  placeholder="e.g. Acme Corporation"
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Organization Slug</label>
                <input
                  type="text"
                  required
                  value={orgForm.slug}
                  onChange={(e) => setOrgForm({ ...orgForm, slug: e.target.value })}
                  placeholder="e.g. acme-corp"
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Primary Domain</label>
                <input
                  type="text"
                  required
                  value={orgForm.domain}
                  onChange={(e) => setOrgForm({ ...orgForm, domain: e.target.value })}
                  placeholder="e.g. acme.com"
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
                <Button type="button" variant="zinc" onClick={() => setShowOrgModal(false)}>
                  Cancel
                </Button>
                <Button type="submit">Create Organization</Button>
              </div>
            </form>
          </div>
        )}

        {/* Modal: Create Workspace */}
        {showWsModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <form onSubmit={handleCreateWorkspace} className="w-full max-w-md rounded-2xl border border-white/10 bg-[#111827] p-6 shadow-2xl space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Globe className="h-5 w-5 text-indigo-400" /> Create Isolated Workspace
              </h3>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Workspace Name</label>
                <input
                  type="text"
                  required
                  value={wsForm.name}
                  onChange={(e) => setWsForm({ ...wsForm, name: e.target.value })}
                  placeholder="e.g. Finance AI Lab"
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Workspace Slug</label>
                <input
                  type="text"
                  required
                  value={wsForm.slug}
                  onChange={(e) => setWsForm({ ...wsForm, slug: e.target.value })}
                  placeholder="e.g. finance-lab"
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
                <Button type="button" variant="zinc" onClick={() => setShowWsModal(false)}>
                  Cancel
                </Button>
                <Button type="submit">Create Workspace</Button>
              </div>
            </form>
          </div>
        )}

        {/* Modal: Invite Member */}
        {showInviteModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <form onSubmit={handleInviteMember} className="w-full max-w-md rounded-2xl border border-white/10 bg-[#111827] p-6 shadow-2xl space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Mail className="h-5 w-5 text-indigo-400" /> Invite Organization Member
              </h3>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Member Email</label>
                <input
                  type="email"
                  required
                  value={inviteForm.email}
                  onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                  placeholder="user@enterprise.com"
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
                <Button type="button" variant="zinc" onClick={() => setShowInviteModal(false)}>
                  Cancel
                </Button>
                <Button type="submit">Send Invitation</Button>
              </div>
            </form>
          </div>
        )}
      </div>
    </AppShell>
  );
}
