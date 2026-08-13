"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { Button } from "../ui";

export default function ProviderConfigModal({
  isOpen,
  onClose,
  provider,
  allProviders = [],
  onSave,
  busy = false,
}) {
  if (!isOpen || !provider) return null;

  const initialBaseUrl = provider.base_url && !provider.base_url.includes("vendor.com") ? provider.base_url : "";

  const [formState, setFormState] = useState({
    api_key: "",
    model: provider.configured_model || "",
    base_url: initialBaseUrl,
    organization_id: provider.organization_id || "",
    timeout_seconds: provider.timeout_seconds || 30,
    retry_count: provider.retry_count || 3,
    rate_limit_rpm: provider.rate_limit_rpm || 600,
    rate_limit_tpm: provider.rate_limit_tpm || 100000,
    priority: provider.priority || 10,
    cost_multiplier: provider.cost_multiplier || 1.0,
    primary_provider_id: provider.primary_provider_id || "",
    secondary_provider_id: provider.secondary_provider_id || "",
    auto_failover: provider.auto_failover ?? true,
  });

  const handleSubmit = () => {
    const payload = { ...formState };
    // If api_key untouched/empty, don't send to keep existing credentials
    if (!payload.api_key || !payload.api_key.trim()) {
      delete payload.api_key;
    }

    // Modal Input Sanitization: Pass base_url as "" if user leaves input blank or uses placeholder
    if (!payload.base_url || !payload.base_url.trim() || payload.base_url.includes("vendor.com")) {
      payload.base_url = "";
    } else {
      payload.base_url = payload.base_url.trim();
    }

    if (payload.model) {
      payload.default_model = payload.model;
    }

    onSave(payload);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
      <div className="surface max-h-[90vh] w-full max-w-xl overflow-y-auto p-6 rounded-2xl border border-white/10 shadow-2xl">
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div>
            <h3 className="text-lg font-bold text-white">
              Configure Provider: {provider.provider_name}
            </h3>
            <p className="text-xs text-slate-400">
              Update runtime credentials, limits, priority, and failover targets
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-4 space-y-4 text-xs">
          {/* API Key */}
          <div>
            <label className="block text-slate-300 font-medium mb-1">
              API Key / Secret Credential
            </label>
            <input
              type="password"
              placeholder={provider.api_key_masked || "Enter new API key..."}
              value={formState.api_key}
              onChange={(e) =>
                setFormState({ ...formState, api_key: e.target.value })
              }
              className="w-full rounded-xl bg-black/40 px-3 py-2 text-xs text-white border border-white/10 outline-none focus:border-indigo-500"
            />
          </div>

          {/* Base URL & Default Model */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Base URL
              </label>
              <input
                type="text"
                placeholder="Official SDK Default Endpoint (leave blank)"
                value={formState.base_url}
                onChange={(e) =>
                  setFormState({ ...formState, base_url: e.target.value })
                }
                className="w-full rounded-xl bg-black/40 px-3 py-2 text-xs text-white border border-white/10 outline-none"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Default Model
              </label>
              <input
                type="text"
                placeholder="gemini-2.0-flash"
                value={formState.model}
                onChange={(e) =>
                  setFormState({ ...formState, model: e.target.value })
                }
                className="w-full rounded-xl bg-black/40 px-3 py-2 text-xs text-white border border-white/10 outline-none"
              />
            </div>
          </div>

          {/* Timeout & Retry Count */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Timeout (Seconds)
              </label>
              <input
                type="number"
                value={formState.timeout_seconds}
                onChange={(e) =>
                  setFormState({
                    ...formState,
                    timeout_seconds: parseInt(e.target.value) || 30,
                  })
                }
                className="w-full rounded-xl bg-black/40 px-3 py-2 text-xs text-white border border-white/10 outline-none"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Max Retry Count
              </label>
              <input
                type="number"
                value={formState.retry_count}
                onChange={(e) =>
                  setFormState({
                    ...formState,
                    retry_count: parseInt(e.target.value) || 3,
                  })
                }
                className="w-full rounded-xl bg-black/40 px-3 py-2 text-xs text-white border border-white/10 outline-none"
              />
            </div>
          </div>

          {/* Priority & Cost Multiplier */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Priority Rank (1 = Highest)
              </label>
              <input
                type="number"
                value={formState.priority}
                onChange={(e) =>
                  setFormState({
                    ...formState,
                    priority: parseInt(e.target.value) || 10,
                  })
                }
                className="w-full rounded-xl bg-black/40 px-3 py-2 text-xs text-white border border-white/10 outline-none"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Cost Multiplier
              </label>
              <input
                type="number"
                step="0.1"
                value={formState.cost_multiplier}
                onChange={(e) =>
                  setFormState({
                    ...formState,
                    cost_multiplier: parseFloat(e.target.value) || 1.0,
                  })
                }
                className="w-full rounded-xl bg-black/40 px-3 py-2 text-xs text-white border border-white/10 outline-none"
              />
            </div>
          </div>

          {/* Secondary Failover Target */}
          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Secondary Failover Target Provider
            </label>
            <select
              value={formState.secondary_provider_id}
              onChange={(e) =>
                setFormState({
                  ...formState,
                  secondary_provider_id: e.target.value,
                })
              }
              className="w-full rounded-xl bg-black/40 px-3 py-2 text-xs text-white border border-white/10 outline-none"
            >
              <option value="">None (Default Resiliency Chain)</option>
              {allProviders
                .filter((p) => p.provider_id !== provider.provider_id)
                .map((p) => (
                  <option key={p.provider_id} value={p.provider_id}>
                    {p.provider_name} ({p.provider_id})
                  </option>
                ))}
            </select>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-white/10">
          <Button variant="secondary" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={busy}>
            {busy ? "Saving..." : "Save Configuration"}
          </Button>
        </div>
      </div>
    </div>
  );
}
