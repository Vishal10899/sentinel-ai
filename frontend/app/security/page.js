"use client";

import { useEffect, useState } from "react";
import { ShieldAlert, ShieldCheck, Lock, Sliders, RefreshCw, Plus, Check } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, Toast } from "../../components/ui";
import WithAdminAuth from "../../components/WithAdminAuth";
import api from "../../lib/api";

function SecurityPoliciesPage() {
  const [policies, setPolicies] = useState([
    { id: "dlp-01", name: "SSN & Credit Card Redaction", type: "DLP / PII", status: "active", action: "redact" },
    { id: "mcp-01", name: "MCP Tool Execution Sandbox", type: "MCP Security", status: "active", action: "isolate" },
    { id: "mcp-02", name: "Restricted File System Access", type: "MCP Security", status: "active", action: "block" },
    { id: "dlp-02", name: "API Key Leak Detection", type: "DLP / PII", status: "active", action: "block" },
  ]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState("");

  const refreshPolicies = async () => {
    setLoading(true);
    try {
      if (api.policies) {
        const res = await api.policies();
        if (res && res.length > 0) setPolicies(res);
      }
      setToast("Security & DLP policies updated.");
    } catch (e) {
      console.warn("Failed to fetch live policies:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell
      title="DLP & MCP Security Policies"
      subtitle="Configure DLP PII redaction rules, MCP tool permissions, and compliance guards"
    >
      <PageTitle
        eyebrow="Security & Governance"
        title="DLP & MCP Security Rules"
        subtitle="Manage active DLP redaction rules and Model Context Protocol (MCP) access controls."
        action={
          <Button onClick={refreshPolicies} variant="secondary" className="text-xs">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh Rules
          </Button>
        }
      />

      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="surface p-4 border border-[var(--border-color)] rounded-xl">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400">
                <ShieldAlert className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">4 Active</p>
                <p className="text-xs text-slate-400">DLP Guardrails</p>
              </div>
            </div>
          </div>

          <div className="surface p-4 border border-[var(--border-color)] rounded-xl">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">Strict</p>
                <p className="text-xs text-slate-400">MCP Tool Governance</p>
              </div>
            </div>
          </div>

          <div className="surface p-4 border border-[var(--border-color)] rounded-xl">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-400">
                <Lock className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">Admin Only</p>
                <p className="text-xs text-slate-400">Policy Management</p>
              </div>
            </div>
          </div>
        </div>

        <div className="surface p-6 border border-[var(--border-color)] rounded-2xl space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Configured Protection Rules</h3>

          <div className="divide-y divide-white/10">
            {policies.map((p) => (
              <div key={p.id} className="py-3.5 flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-white">{p.name}</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">Category: {p.type} | ID: {p.id}</p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge tone={p.status === "active" ? "green" : "amber"}>{p.status}</Badge>
                  <span className="text-xs font-mono bg-white/5 border border-white/10 px-2.5 py-1 rounded text-indigo-300">
                    Action: {p.action}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {toast && <Toast message={toast} clear={() => setToast("")} />}
    </AppShell>
  );
}

export default WithAdminAuth(SecurityPoliciesPage);
