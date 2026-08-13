"use client";

import { useEffect, useState } from "react";
import { Users, UserPlus, Mail, Shield, CheckCircle2, AlertCircle, RefreshCw } from "lucide-react";
import { AppShell, PageTitle } from "../../../components/shell";
import { Badge, Button, Toast } from "../../../components/ui";
import WithAdminAuth from "../../../components/WithAdminAuth";
import api from "../../../lib/api";

function TeamManagementPage() {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState("");
  const [form, setForm] = useState({
    email: "",
    role: "DEVELOPER",
  });

  const loadMembers = async () => {
    setLoading(true);
    try {
      if (api.getTeamMembers) {
        const data = await api.getTeamMembers();
        if (data && Array.isArray(data)) {
          setMembers(data);
        }
      }
    } catch (e) {
      console.warn("Could not load members:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMembers();
  }, []);

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!form.email) return;

    setSubmitting(true);
    try {
      const res = await api.inviteTeamMember({
        email: form.email,
        role: form.role,
      });

      setToast(res.message || `Invitation sent to ${form.email}`);
      setForm({ email: "", role: "DEVELOPER" });
      loadMembers();
    } catch (err) {
      setToast(`Invite failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AppShell
      title="Team & Member Management"
      subtitle="Invite members, manage workspace access roles, & audit security permissions"
    >
      <PageTitle
        eyebrow="Workspace Administration"
        title="Team & Member Access Control"
        subtitle="Manage workspace members and send new invitations with default DEVELOPER or MEMBER roles."
        action={
          <Button onClick={loadMembers} variant="secondary" className="text-xs">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
          </Button>
        }
      />

      <div className="space-y-6">
        {/* Invite New Team Member Form Card */}
        <div className="surface p-6 border border-[var(--border-color)] rounded-2xl space-y-4">
          <div className="flex items-center gap-2">
            <UserPlus className="h-5 w-5 text-indigo-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Invite New Team Member</h3>
          </div>

          <form onSubmit={handleInvite} className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-1">
              <label className="block text-xs text-slate-300 font-medium mb-1">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                <input
                  type="email"
                  required
                  placeholder="colleague@company.com"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="w-full rounded-xl bg-black/40 pl-9 pr-3.5 py-2.5 text-xs text-white border border-white/10 outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs text-slate-300 font-medium mb-1">Assign Role</label>
              <select
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="w-full rounded-xl bg-[#121827] px-3.5 py-2.5 text-xs text-white border border-white/10 outline-none focus:border-indigo-500"
              >
                <option value="DEVELOPER">DEVELOPER (Prompting & Playground)</option>
                <option value="MEMBER">MEMBER (Read-only Viewer)</option>
              </select>
            </div>

            <div className="flex items-end">
              <Button type="submit" disabled={submitting} className="w-full">
                {submitting ? "Sending Invite..." : "Send Invitation"}
              </Button>
            </div>
          </form>
        </div>

        {/* Workspace Members List Table */}
        <div className="surface p-6 border border-[var(--border-color)] rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Users className="h-4 w-4 text-indigo-400" /> Active Workspace Members ({members.length})
            </h3>
          </div>

          <div className="divide-y divide-white/10">
            {members.length === 0 ? (
              <p className="text-xs text-slate-400 py-4 text-center">No team members loaded yet.</p>
            ) : (
              members.map((m) => (
                <div key={m.id} className="py-3.5 flex items-center justify-between">
                  <div>
                    <h4 className="text-xs font-bold text-white">{m.name}</h4>
                    <p className="text-[11px] font-mono text-slate-400 mt-0.5">{m.email}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge tone={m.role === "ADMIN" ? "purple" : "indigo"}>
                      {m.role}
                    </Badge>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {toast && <Toast message={toast} clear={() => setToast("")} />}
    </AppShell>
  );
}

export default WithAdminAuth(TeamManagementPage);
