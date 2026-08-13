"use client";

import { useEffect, useState } from "react";
import { ShieldCheck, Plus, Trash2, CheckCircle, AlertTriangle, Lock, Sliders, Zap } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import { api } from "../../lib/api";

export default function PoliciesPage() {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    max_tokens: 4096,
    max_temperature: 1.0,
    monthly_budget_limit_usd: "",
    blocked_providers: "",
    blocked_models: "",
  });

  const loadPolicies = async () => {
    try {
      setLoading(true);
      const data = await api.getPolicies();
      setPolicies(data || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, []);

  const handleCreatePolicy = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: formData.name,
        description: formData.description,
        max_tokens: parseInt(formData.max_tokens, 10) || 4096,
        max_temperature: parseFloat(formData.max_temperature) || 1.0,
        monthly_budget_limit_usd: formData.monthly_budget_limit_usd ? parseFloat(formData.monthly_budget_limit_usd) : null,
        blocked_providers: formData.blocked_providers ? formData.blocked_providers.split(",").map((s) => s.trim()) : [],
        blocked_models: formData.blocked_models ? formData.blocked_models.split(",").map((s) => s.trim()) : [],
        is_active: true,
      };

      await api.createPolicy(payload);
      setToast({ type: "success", message: "Policy created successfully!" });
      setShowModal(false);
      loadPolicies();
    } catch (err) {
      setToast({ type: "error", message: `Failed to create policy: ${err.message}` });
    }
  };

  const handleDeletePolicy = async (id) => {
    if (!confirm("Are you sure you want to delete this policy?")) return;
    try {
      await api.deletePolicy(id);
      setToast({ type: "success", message: "Policy deleted." });
      loadPolicies();
    } catch (err) {
      setToast({ type: "error", message: `Failed: ${err.message}` });
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageTitle
          title="Enterprise Governance Policies"
          subtitle="Define security boundaries, parameter caps, provider restrictions, and monthly AI budgets."
          action={
            <Button onClick={() => setShowModal(true)}>
              <Plus className="h-4 w-4" /> New Policy
            </Button>
          }
        />

        {toast && <Toast type={toast.type} message={toast.message} onClose={() => setToast(null)} />}

        {loading ? (
          <LoadingCard title="Loading Governance Policies..." />
        ) : error ? (
          <ErrorCard title="Policy Load Error" message={error} onRetry={loadPolicies} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {policies.map((p) => (
              <div
                key={p.id}
                className="surface flex flex-col justify-between rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl hover:border-indigo-500/40 transition"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="flex items-center gap-2 font-bold text-white text-sm">
                      <ShieldCheck className="h-4 w-4 text-emerald-400" /> {p.name}
                    </span>
                    <Badge variant={p.is_active ? "emerald" : "zinc"}>
                      {p.is_active ? "Active" : "Disabled"}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-400 line-clamp-2 mb-4">
                    {p.description || "Workspace request governance policy."}
                  </p>

                  <div className="space-y-2 text-xs text-slate-300 border-t border-white/10 pt-3">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Max Tokens:</span>
                      <span className="font-mono font-semibold text-indigo-300">{p.max_tokens ?? "Unlimited"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Max Temp:</span>
                      <span className="font-mono font-semibold text-indigo-300">{p.max_temperature ?? "1.0"}</span>
                    </div>
                    {p.monthly_budget_limit_usd && (
                      <div className="flex justify-between">
                        <span className="text-slate-400">Monthly Budget:</span>
                        <span className="font-mono font-bold text-emerald-400">${p.monthly_budget_limit_usd.toFixed(2)}</span>
                      </div>
                    )}
                    {p.blocked_providers?.length > 0 && (
                      <div className="flex justify-between">
                        <span className="text-slate-400">Blocked Providers:</span>
                        <span className="font-mono text-rose-300 truncate max-w-[140px]">{p.blocked_providers.join(", ")}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-5 border-t border-white/10 pt-3 flex justify-end">
                  <button
                    onClick={() => handleDeletePolicy(p.id)}
                    className="p-1.5 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-rose-500/10 transition"
                    title="Delete Policy"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal Create Form */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <form onSubmit={handleCreatePolicy} className="w-full max-w-lg rounded-2xl border border-white/10 bg-[#111827] p-6 shadow-2xl space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-indigo-400" /> Create Governance Policy
              </h3>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Policy Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Engineering Team Strict Governance"
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Description</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Brief policy explanation..."
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Max Tokens Cap</label>
                  <input
                    type="number"
                    value={formData.max_tokens}
                    onChange={(e) => setFormData({ ...formData, max_tokens: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Max Temperature</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    value={formData.max_temperature}
                    onChange={(e) => setFormData({ ...formData, max_temperature: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Monthly Budget Limit ($ USD)</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.monthly_budget_limit_usd}
                  onChange={(e) => setFormData({ ...formData, monthly_budget_limit_usd: e.target.value })}
                  placeholder="Optional budget limit e.g. 50.00"
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Blocked Providers (Comma-separated)</label>
                <input
                  type="text"
                  value={formData.blocked_providers}
                  onChange={(e) => setFormData({ ...formData, blocked_providers: e.target.value })}
                  placeholder="e.g. untrusted-provider, mock-provider"
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
                <Button type="button" variant="zinc" onClick={() => setShowModal(false)}>
                  Cancel
                </Button>
                <Button type="submit">Create Policy</Button>
              </div>
            </form>
          </div>
        )}
      </div>
    </AppShell>
  );
}
