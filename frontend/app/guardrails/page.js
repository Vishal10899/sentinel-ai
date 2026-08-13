"use client";

import { useEffect, useState } from "react";
import { ShieldAlert, Lock, Eye, AlertTriangle, CheckCircle2, RefreshCw, Terminal, Search } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import { api } from "../../lib/api";

export default function GuardrailsPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Live Threat Simulator State
  const [testPrompt, setTestPrompt] = useState("");
  const [scanResult, setScanResult] = useState(null);
  const [scanning, setScanning] = useState(false);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await api.getGuardrailStats();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const handleScanPrompt = async (e) => {
    e.preventDefault();
    if (!testPrompt.trim()) return;
    try {
      setScanning(true);
      const res = await api.scanPrompt({ prompt: testPrompt });
      setScanResult(res);
    } catch (err) {
      alert(`Scan failed: ${err.message}`);
    } finally {
      setScanning(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageTitle
          title="AI Guardrails & Threat Defense"
          subtitle="Real-time protection against Prompt Injections, DAN Jailbreaks, PII leakage, and exposed API key secrets."
          action={
            <Button variant="zinc" onClick={loadStats}>
              <RefreshCw className="h-4 w-4" /> Refresh Telemetry
            </Button>
          }
        />

        {loading ? (
          <LoadingCard title="Loading Security Telemetry..." />
        ) : error ? (
          <ErrorCard title="Telemetry Load Error" message={error} onRetry={loadStats} />
        ) : (
          <>
            {/* Top Threat Metrics Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl">
                <div className="flex items-center justify-between text-slate-400 text-xs">
                  <span>Prompt Injections</span>
                  <ShieldAlert className="h-4 w-4 text-amber-400" />
                </div>
                <p className="text-2xl font-extrabold text-white mt-2">{stats?.prompt_injections_detected || 0}</p>
                <p className="text-[11px] text-amber-400 mt-1">Override & leakage attacks blocked</p>
              </div>

              <div className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl">
                <div className="flex items-center justify-between text-slate-400 text-xs">
                  <span>Jailbreaks Detected</span>
                  <Lock className="h-4 w-4 text-rose-400" />
                </div>
                <p className="text-2xl font-extrabold text-rose-400 mt-2">{stats?.jailbreaks_detected || 0}</p>
                <p className="text-[11px] text-slate-400 mt-1">DAN & safety persona bypasses</p>
              </div>

              <div className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl">
                <div className="flex items-center justify-between text-slate-400 text-xs">
                  <span>PII Redactions</span>
                  <Eye className="h-4 w-4 text-indigo-400" />
                </div>
                <p className="text-2xl font-extrabold text-indigo-300 mt-2">{stats?.pii_redactions || 0}</p>
                <p className="text-[11px] text-indigo-400 mt-1">Emails, Credit Cards & SSNs masked</p>
              </div>

              <div className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl">
                <div className="flex items-center justify-between text-slate-400 text-xs">
                  <span>Secrets Masked</span>
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                </div>
                <p className="text-2xl font-extrabold text-emerald-400 mt-2">{stats?.secrets_masked || 0}</p>
                <p className="text-[11px] text-slate-400 mt-1">AWS, OpenAI & Gemini keys sanitized</p>
              </div>
            </div>

            {/* Live Prompt Threat Testing Tool */}
            <div className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Terminal className="h-4 w-4 text-indigo-400" /> Live AI Guardrail Threat Scanner
              </h3>
              <p className="text-xs text-slate-400">
                Test prompt injection vectors, jailbreaks, or PII text to inspect real-time guardrail sanitization.
              </p>

              <form onSubmit={handleScanPrompt} className="space-y-3">
                <textarea
                  rows={3}
                  value={testPrompt}
                  onChange={(e) => setTestPrompt(e.target.value)}
                  placeholder="Paste prompt or secret e.g. 'Ignore previous rules. Contact me at user@example.com or sk-1234567890abcdef1234567890abcdef1234567890abcdef'..."
                  className="w-full rounded-xl border border-white/10 bg-black/40 p-3 text-xs text-white outline-none focus:border-indigo-500"
                />
                <Button type="submit" disabled={scanning || !testPrompt.trim()}>
                  {scanning ? "Scanning Threat Vector..." : "Run Guardrail Scan"}
                </Button>
              </form>

              {scanResult && (
                <div className="mt-4 rounded-xl border border-white/10 bg-black/30 p-4 space-y-3 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-300">Action:</span>
                    <Badge variant={scanResult.action === "BLOCK" ? "rose" : scanResult.action === "SANITIZE" ? "indigo" : "emerald"}>
                      {scanResult.action}
                    </Badge>
                  </div>

                  <div>
                    <span className="font-semibold text-slate-300 block mb-1">Adversarial Risk Score:</span>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
                        <div
                          className={`h-full ${scanResult.risk_score >= 0.8 ? "bg-rose-500" : scanResult.risk_score >= 0.4 ? "bg-amber-500" : "bg-emerald-500"}`}
                          style={{ width: `${scanResult.risk_score * 100}%` }}
                        />
                      </div>
                      <span className="font-mono text-white font-bold">{(scanResult.risk_score * 100).toFixed(0)}%</span>
                    </div>
                  </div>

                  {scanResult.matched_rules?.length > 0 && (
                    <div>
                      <span className="font-semibold text-amber-300 block">Matched Threat Rules:</span>
                      <p className="font-mono text-amber-200 text-[11px] mt-0.5">{scanResult.matched_rules.join(", ")}</p>
                    </div>
                  )}

                  <div>
                    <span className="font-semibold text-slate-300 block mb-1">Sanitized Output:</span>
                    <div className="rounded-lg bg-black/50 p-2.5 font-mono text-[11px] text-emerald-300 whitespace-pre-wrap">
                      {scanResult.sanitized_text}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
