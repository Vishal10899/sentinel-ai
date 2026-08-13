"use client";

import { useEffect, useState } from "react";
import { Key, Plus, RefreshCw, Copy, CheckCircle2, ShieldCheck, Trash2, SlidersHorizontal, Lock, Eye, AlertTriangle } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard, Toast, EmptyState } from "../../components/ui";
import { api } from "../../lib/api";

export default function VirtualKeysPage() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [newKeySecret, setNewKeySecret] = useState(null);
  const [creating, setCreating] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    workspace_id: "default",
    key_type: "WORKSPACE",
    allowed_providers: "",
    allowed_models: "",
  });

  const loadKeys = async () => {
    try {
      setLoading(true);
      const data = await api.getVirtualKeys();
      setKeys(data || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadKeys();
  }, []);

  const handleCreateKey = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) return;

    try {
      setCreating(true);
      const payload = {
        name: formData.name.trim(),
        workspace_id: formData.workspace_id,
        key_type: formData.key_type,
        allowed_providers: formData.allowed_providers
          ? formData.allowed_providers.split(",").map((s) => s.trim()).filter(Boolean)
          : [],
        allowed_models: formData.allowed_models
          ? formData.allowed_models.split(",").map((s) => s.trim()).filter(Boolean)
          : [],
      };

      const res = await api.createVirtualKey(payload);
      setNewKeySecret(res.secret_key);
      setShowModal(false);
      setFormData({
        name: "",
        workspace_id: "default",
        key_type: "WORKSPACE",
        allowed_providers: "",
        allowed_models: "",
      });
      setToast({ type: "success", message: "Virtual API Key generated successfully." });
      loadKeys();
    } catch (err) {
      setToast({ type: "error", message: `Generation failed: ${err.message}` });
    } finally {
      setCreating(false);
    }
  };

  const handleRotateKey = async (keyId) => {
    if (!confirm("Are you sure you want to rotate this key? The existing secret token will be revoked immediately.")) return;
    try {
      const res = await api.rotateVirtualKey(keyId);
      setNewKeySecret(res.secret_key);
      setToast({ type: "success", message: "Virtual Key secret rotated." });
      loadKeys();
    } catch (err) {
      setToast({ type: "error", message: `Rotation failed: ${err.message}` });
    }
  };

  const handleRevokeKey = async (keyId) => {
    if (!confirm("Are you sure you want to revoke this key? Active services using this key will fail immediately.")) return;
    try {
      await api.revokeVirtualKey(keyId);
      setToast({ type: "success", message: "Virtual Key revoked." });
      loadKeys();
    } catch (err) {
      setToast({ type: "error", message: `Revocation failed: ${err.message}` });
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setToast({ type: "success", message: "Secret key copied to clipboard." });
    } catch {
      setToast({ type: "error", message: "Failed to access clipboard." });
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageTitle
          eyebrow="Security & Credential Management"
          title="Virtual API Keys"
          subtitle="Scope-restricted virtual tokens that conceal upstream LLM provider credentials and enforce spend limits."
          action={
            <Button onClick={() => setShowModal(true)}>
              <Plus className="h-4 w-4" /> Issue Virtual Key
            </Button>
          }
        />

        {toast && <Toast type={toast.type} message={toast.message} onClose={() => setToast(null)} />}

        {/* Secret Key Revealed Prompt Modal */}
        {newKeySecret && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
            <div className="w-full max-w-lg rounded-2xl border border-emerald-500/40 bg-[#0c1410] p-6 shadow-2xl space-y-4">
              <div className="flex items-center gap-2.5 text-emerald-400 font-bold text-sm">
                <CheckCircle2 className="h-5 w-5" /> Virtual Key Created — One-Time Secret Reveal
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Copy your secret key now. For zero-trust security, Sentinel AI hashes secret tokens immediately after creation and cannot retrieve it again.
              </p>
              <div className="flex items-center justify-between rounded-xl border border-emerald-500/30 bg-black/60 p-3 font-mono text-xs text-emerald-300 break-all">
                <span>{newKeySecret}</span>
                <button
                  onClick={() => copyToClipboard(newKeySecret)}
                  className="p-1.5 text-slate-400 hover:text-white shrink-0 ml-2 rounded hover:bg-white/10"
                  title="Copy to Clipboard"
                >
                  <Copy className="h-4 w-4" />
                </button>
              </div>
              <div className="flex justify-end pt-2">
                <Button variant="emerald" onClick={() => setNewKeySecret(null)} className="w-full">
                  I Have Saved My Key Safely
                </Button>
              </div>
            </div>
          </div>
        )}

        {loading ? (
          <LoadingCard label="Loading Virtual Key Registry..." />
        ) : error ? (
          <ErrorCard title="Virtual Keys Registry Error" message={error} onRetry={loadKeys} />
        ) : keys.length === 0 ? (
          <EmptyState
            icon={Key}
            title="No Virtual API Keys Issued"
            copy="Generate a scope-restricted Virtual API Key to authorize applications without exposing raw provider API keys."
            actionText="Issue Virtual Key"
            onAction={() => setShowModal(true)}
          />
        ) : (
          <div className="surface overflow-hidden">
            <div className="p-4 border-b border-white/[0.08] flex items-center justify-between bg-white/[0.01]">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                <Lock className="h-4 w-4 text-indigo-400" />
                <span>Active Credentials ({keys.length})</span>
              </div>
              <Badge tone="indigo">Zero-Trust Hashing Enforced</Badge>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="border-b border-white/[0.08] bg-white/[0.02] uppercase text-[10px] text-slate-400 font-bold tracking-wider font-mono">
                  <tr>
                    <th className="p-3.5 pl-4">Key Name</th>
                    <th className="p-3.5">Key Prefix</th>
                    <th className="p-3.5">Key Type</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5">Requests</th>
                    <th className="p-3.5">Allowed Providers</th>
                    <th className="p-3.5 text-right pr-4">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.06]">
                  {keys.map((k) => (
                    <tr key={k.id} className="hover:bg-white/[0.02] transition">
                      <td className="p-3.5 pl-4 font-semibold text-white flex items-center gap-2">
                        <Key className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
                        <span>{k.name}</span>
                      </td>
                      <td className="p-3.5 font-mono text-slate-400">{k.prefix}</td>
                      <td className="p-3.5">
                        <Badge tone={k.key_type === "WORKSPACE" ? "indigo" : k.key_type === "SERVICE" ? "cyan" : "zinc"}>
                          {k.key_type}
                        </Badge>
                      </td>
                      <td className="p-3.5">
                        <Badge tone={k.is_active ? "green" : "rose"}>
                          {k.is_active ? "Active" : "Revoked"}
                        </Badge>
                      </td>
                      <td className="p-3.5 font-mono text-slate-300">{k.usage_count || 0} reqs</td>
                      <td className="p-3.5 font-mono text-slate-400">
                        {k.allowed_providers && k.allowed_providers.length > 0
                          ? k.allowed_providers.join(", ")
                          : "All Providers"}
                      </td>
                      <td className="p-3.5 text-right pr-4 space-x-1">
                        {k.is_active && (
                          <button
                            onClick={() => handleRotateKey(k.id)}
                            className="p-1.5 text-slate-400 hover:text-indigo-300 rounded hover:bg-indigo-500/10 transition"
                            title="Rotate Key Secret"
                          >
                            <RefreshCw className="h-3.5 w-3.5" />
                          </button>
                        )}
                        {k.is_active && (
                          <button
                            onClick={() => handleRevokeKey(k.id)}
                            className="p-1.5 text-slate-400 hover:text-rose-400 rounded hover:bg-rose-500/10 transition"
                            title="Revoke Key"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal Create Form */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <form onSubmit={handleCreateKey} className="w-full max-w-lg rounded-2xl border border-white/10 bg-[#121824] p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Key className="h-4 w-4 text-indigo-400" /> Issue Virtual API Key
                </h3>
                <button type="button" onClick={() => setShowModal(false)} className="text-slate-400 hover:text-white">
                  ✕
                </button>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Key Label / Service Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Analytics Ingestion Worker"
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 font-medium"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Key Scope Type</label>
                  <select
                    value={formData.key_type}
                    onChange={(e) => setFormData({ ...formData, key_type: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 font-medium"
                  >
                    <option value="WORKSPACE">WORKSPACE</option>
                    <option value="SERVICE">SERVICE</option>
                    <option value="TEMPORARY">TEMPORARY</option>
                    <option value="READONLY">READONLY</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Workspace ID</label>
                  <input
                    type="text"
                    value={formData.workspace_id}
                    onChange={(e) => setFormData({ ...formData, workspace_id: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Allowed Providers (Comma-separated)</label>
                <input
                  type="text"
                  value={formData.allowed_providers}
                  onChange={(e) => setFormData({ ...formData, allowed_providers: e.target.value })}
                  placeholder="e.g. openai, gemini, anthropic (Leave blank for all)"
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Allowed Models (Comma-separated)</label>
                <input
                  type="text"
                  value={formData.allowed_models}
                  onChange={(e) => setFormData({ ...formData, allowed_models: e.target.value })}
                  placeholder="e.g. gpt-4o, gemini-1.5-pro (Leave blank for all)"
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 font-mono"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-white/10">
                <Button type="button" variant="ghost" onClick={() => setShowModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" isLoading={creating}>
                  Issue Key Token
                </Button>
              </div>
            </form>
          </div>
        )}
      </div>
    </AppShell>
  );
}
