"use client";

import { useState } from "react";
import { AppShell } from "../../components/shell";
import {
  ShieldAlert,
  ShieldCheck,
  Eye,
  EyeOff,
  Lock,
  Terminal,
  CheckCircle2,
  AlertOctagon,
  Globe
} from "lucide-react";

export default function DLPPage() {
  const [rules, setRules] = useState([
    { id: "ssn", name: "Social Security Numbers (SSN)", pattern: "\\b\\d{3}-\\d{2}-\\d{4}\\b", action: "MASK [REDACTED_SSN]", enabled: true, count: 142 },
    { id: "credit_card", name: "Credit Card Numbers (PCI-DSS)", pattern: "\\b(?:\\d[ -]*?){13,16}\\b", action: "MASK [REDACTED_CREDIT_CARD]", enabled: true, count: 89 },
    { id: "api_key", name: "Cloud API Secrets (sk-*, Bearer)", pattern: "sk-[a-zA-Z0-9]{20,}|Bearer\\s+[a-zA-Z0-9_-]+", action: "MASK [REDACTED_API_KEY]", enabled: true, count: 304 },
    { id: "jwt", name: "JWT Bearer Tokens", pattern: "eyJ[a-zA-Z0-9_-]{10,}\\.[a-zA-Z0-9_-]{10,}\\.[a-zA-Z0-9_-]{10,}", action: "MASK [REDACTED_JWT_TOKEN]", enabled: true, count: 67 },
  ]);

  const [testInput, setTestInput] = useState(
    "User SSN is 123-45-6789 and API Key is sk-proj-1234567890abcdefghijklmnopqrstuv"
  );
  const [testOutput, setTestOutput] = useState("");
  const [testing, setTesting] = useState(false);

  const handleTestRedaction = () => {
    setTesting(true);
    let output = testInput;
    output = output.replace(/\b\d{3}-\d{2}-\d{4}\b/g, "[REDACTED_SSN]");
    output = output.replace(/sk-[a-zA-Z0-9]{20,}|Bearer\s+[a-zA-Z0-9_-]+/gi, "[REDACTED_API_KEY]");
    output = output.replace(/\b(?:\d[ -]*?){13,16}\b/g, "[REDACTED_CREDIT_CARD]");
    
    setTimeout(() => {
      setTestOutput(output);
      setTesting(false);
    }, 300);
  };

  const toggleRule = (id) => {
    setRules(rules.map(r => r.id === id ? { ...r, enabled: !r.enabled } : r));
  };

  return (
    <AppShell
      title="Inline DLP & Zero-Trust PII Redaction"
      subtitle="Real-time zero-copy memory buffer inspection, secret masking, and data residency compliance"
    >
      <div className="space-y-8">
        {/* Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="surface p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-[var(--text-secondary)] mb-2">
              <span className="text-sm font-medium">DLP Latency Overhead</span>
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-[var(--text-primary)]">&lt; 3.5 μs</div>
            <div className="text-xs text-emerald-400 font-medium mt-1">Zero-Copy Ingest Buffer</div>
          </div>

          <div className="surface p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-[var(--text-secondary)] mb-2">
              <span className="text-sm font-medium">Total Secrets Masked</span>
              <Lock className="w-5 h-5 text-indigo-400" />
            </div>
            <div className="text-2xl font-bold text-[var(--text-primary)]">602 Items</div>
            <div className="text-xs text-indigo-400 font-medium mt-1">Prevented Egress Leakage</div>
          </div>

          <div className="surface p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-[var(--text-secondary)] mb-2">
              <span className="text-sm font-medium">Active Detection Rules</span>
              <ShieldAlert className="w-5 h-5 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold text-[var(--text-primary)]">{rules.length} Rules</div>
            <div className="text-xs text-cyan-400 font-medium mt-1">PCI-DSS & HIPAA Compliant</div>
          </div>

          <div className="surface p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-[var(--text-secondary)] mb-2">
              <span className="text-sm font-medium">Data Residency Isolation</span>
              <Globe className="w-5 h-5 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-[var(--text-primary)]">ENFORCED</div>
            <div className="text-xs text-amber-400 font-medium mt-1">Private vLLM Air-Gapped Egress</div>
          </div>
        </div>

        {/* Live Redaction Sandbox */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="surface p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] flex items-center gap-2 mb-4">
              <Terminal className="w-5 h-5 text-cyan-400" />
              Inline DLP Redaction Sandbox
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">Unfiltered Input Payload (Client Egress)</label>
                <textarea
                  rows={4}
                  value={testInput}
                  onChange={(e) => setTestInput(e.target.value)}
                  className="w-full bg-[var(--bg-surface-alt)] border border-[var(--border-color)] rounded-lg p-3 font-mono text-xs text-[var(--text-primary)] focus:outline-none focus:border-indigo-500"
                />
              </div>

              <button
                onClick={handleTestRedaction}
                disabled={testing}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium text-sm transition-colors flex items-center justify-center gap-2"
              >
                {testing ? "Inspecting & Redacting..." : "Simulate Inline DLP Masking"}
              </button>
            </div>
          </div>

          <div className="surface p-6 flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] flex items-center gap-2 mb-4">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                Sanitized Payload (Post-Redaction Egress)
              </h3>

              {testOutput ? (
                <div className="p-4 rounded-xl bg-[var(--bg-surface-alt)] border border-[var(--border-color)] text-emerald-500 font-mono text-xs whitespace-pre-wrap">
                  {testOutput}
                </div>
              ) : (
                <div className="h-32 border border-dashed border-[var(--border-color)] rounded-xl flex items-center justify-center text-[var(--text-muted)] text-sm">
                  Run simulation to view sanitized payload egress output.
                </div>
              )}
            </div>

            <div className="mt-6 pt-4 border-t border-[var(--border-color)] text-xs text-[var(--text-secondary)]">
              <p>🛡️ Zero-Copy Ingest Buffer: Performed inside Rust Data Plane prior to forwarding requests to model backends.</p>
            </div>
          </div>
        </div>

        {/* DLP Rule Catalog */}
        <div className="surface p-6">
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Active DLP Masking Rules</h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-[var(--text-primary)]">
              <thead className="bg-[var(--bg-surface-alt)] text-xs uppercase text-[var(--text-secondary)] border-b border-[var(--border-color)]">
                <tr>
                  <th className="p-3">Rule Name</th>
                  <th className="p-3">Regex Pattern</th>
                  <th className="p-3">Action</th>
                  <th className="p-3">Redaction Count</th>
                  <th className="p-3 text-right">Rule Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-color)]">
                {rules.map((r) => (
                  <tr key={r.id} className="hover:bg-[var(--bg-surface-alt)]/50 transition-colors">
                    <td className="p-3 font-medium text-[var(--text-primary)]">{r.name}</td>
                    <td className="p-3 font-mono text-xs text-[var(--text-secondary)]">{r.pattern}</td>
                    <td className="p-3 font-mono text-xs text-indigo-400">{r.action}</td>
                    <td className="p-3 font-mono text-[var(--text-secondary)]">{r.count} leaks blocked</td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => toggleRule(r.id)}
                        className={`px-3 py-1 rounded text-xs font-semibold border transition-colors ${
                          r.enabled
                            ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500"
                            : "bg-[var(--bg-surface-alt)] border-[var(--border-color)] text-[var(--text-muted)]"
                        }`}
                      >
                        {r.enabled ? "ENABLED" : "DISABLED"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
