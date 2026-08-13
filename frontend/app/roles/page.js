"use client";

import { useEffect, useState } from "react";
import { Users, Shield, Plus, Lock, CheckCircle2, XCircle, Trash2, Sliders } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import { api } from "../../lib/api";

export default function RolesPage() {
  const [roles, setRoles] = useState([]);
  const [matrix, setMatrix] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    selectedPermissions: [],
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [rolesData, matrixData] = await Promise.all([
        api.getRoles(),
        api.getPermissionMatrix(),
      ]);
      setRoles(rolesData || []);
      setMatrix(matrixData || null);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTogglePermission = (perm) => {
    setFormData((prev) => {
      const exists = prev.selectedPermissions.includes(perm);
      return {
        ...prev,
        selectedPermissions: exists
          ? prev.selectedPermissions.filter((p) => p !== perm)
          : [...prev.selectedPermissions, perm],
      };
    });
  };

  const handleCreateRole = async (e) => {
    e.preventDefault();
    try {
      await api.createRole({
        name: formData.name,
        description: formData.description,
        permissions: formData.selectedPermissions,
      });
      setToast({ type: "success", message: "Custom role created successfully!" });
      setShowModal(false);
      loadData();
    } catch (err) {
      setToast({ type: "error", message: `Failed: ${err.message}` });
    }
  };

  const handleDeleteRole = async (roleId) => {
    if (!confirm("Are you sure you want to delete this custom role?")) return;
    try {
      await api.deleteRole(roleId);
      setToast({ type: "success", message: "Role deleted." });
      loadData();
    } catch (err) {
      setToast({ type: "error", message: `Failed: ${err.message}` });
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageTitle
          title="Enterprise Roles & RBAC Matrix"
          subtitle="Define role-based access control policies and granular permission matrices for workspace members."
          action={
            <Button onClick={() => setShowModal(true)}>
              <Plus className="h-4 w-4" /> Create Custom Role
            </Button>
          }
        />

        {toast && <Toast type={toast.type} message={toast.message} onClose={() => setToast(null)} />}

        {loading ? (
          <LoadingCard title="Loading Roles & Permission Matrix..." />
        ) : error ? (
          <ErrorCard title="Roles Load Error" message={error} onRetry={loadData} />
        ) : (
          <>
            {/* Roles Inventory Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {roles.map((r) => (
                <div
                  key={r.id}
                  className="surface flex flex-col justify-between rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl hover:border-indigo-500/40 transition"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="flex items-center gap-2 font-bold text-white text-sm">
                        <Shield className="h-4 w-4 text-indigo-400" /> {r.name}
                      </span>
                      <Badge variant={r.is_builtin ? "emerald" : "indigo"}>
                        {r.is_builtin ? "Built-in" : "Custom"}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-2 mb-4">{r.description}</p>

                    <div className="flex flex-wrap gap-1 border-t border-white/10 pt-3">
                      {r.permissions.map((p) => (
                        <span key={p} className="rounded bg-indigo-500/10 px-2 py-0.5 font-mono text-[10px] text-indigo-300">
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>

                  {!r.is_builtin && (
                    <div className="mt-4 border-t border-white/10 pt-3 flex justify-end">
                      <button
                        onClick={() => handleDeleteRole(r.id)}
                        className="p-1 text-slate-400 hover:text-rose-400 rounded hover:bg-rose-500/10"
                        title="Delete Role"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Permission Capabilities Matrix Table */}
            {matrix && (
              <div className="surface rounded-2xl border border-white/10 bg-[#111827] shadow-xl overflow-hidden p-6 space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Sliders className="h-4 w-4 text-indigo-400" /> Permission Matrix Viewer
                </h3>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="border-b border-white/10 bg-white/[0.02] uppercase text-[10px] text-slate-400 font-bold">
                      <tr>
                        <th className="p-3">Permission Scope</th>
                        {roles.map((r) => (
                          <th key={r.id} className="p-3 text-center">{r.name}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/10 font-mono text-[11px]">
                      {matrix.all_permissions.map((perm) => (
                        <tr key={perm} className="hover:bg-white/[0.02]">
                          <td className="p-3 font-semibold text-indigo-300">{perm}</td>
                          {roles.map((r) => {
                            const has = r.permissions.includes("*") || r.permissions.includes("admin") || r.permissions.includes(perm);
                            return (
                              <td key={r.id} className="p-3 text-center">
                                {has ? (
                                  <CheckCircle2 className="h-4 w-4 text-emerald-400 inline" />
                                ) : (
                                  <XCircle className="h-4 w-4 text-slate-600 inline" />
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}

        {/* Create Custom Role Modal */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <form onSubmit={handleCreateRole} className="w-full max-w-xl rounded-2xl border border-white/10 bg-[#111827] p-6 shadow-2xl space-y-4 max-h-[85vh] flex flex-col">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Plus className="h-5 w-5 text-indigo-400" /> Create Custom Role
              </h3>

              <div className="space-y-3 flex-1 overflow-y-auto pr-1">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Role Name</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g. Data Scientist / ML Engineer"
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Description</label>
                  <input
                    type="text"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Role responsibilities..."
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-2">Assigned Permissions</label>
                  <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto rounded-xl border border-white/10 bg-black/30 p-3">
                    {matrix?.all_permissions?.map((perm) => (
                      <label key={perm} className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer hover:text-white">
                        <input
                          type="checkbox"
                          checked={formData.selectedPermissions.includes(perm)}
                          onChange={() => handleTogglePermission(perm)}
                          className="rounded border-white/10 bg-black text-indigo-500"
                        />
                        <span className="font-mono text-[11px]">{perm}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
                <Button type="button" variant="zinc" onClick={() => setShowModal(false)}>
                  Cancel
                </Button>
                <Button type="submit">Create Role</Button>
              </div>
            </form>
          </div>
        )}
      </div>
    </AppShell>
  );
}
