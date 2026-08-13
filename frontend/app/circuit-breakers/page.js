"use client";

import { useState } from "react";
import { AppShell } from "../../components/shell";
import {
  Activity,
  Zap,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Sliders,
  ShieldCheck,
  Server
} from "lucide-react";

export default function CircuitBreakersPage() {
  const [providers, setProviders] = useState([
    { id: "openai", name: "OpenAI Cloud", status: "CLOSED (HEALTHY)", latency_ms: 240, failure_rate: 0.1, ttft_ms: 320, state: "CLOSED" },
    { id: "gemini", name: "Google Gemini", status: "CLOSED (HEALTHY)", latency_ms: 180, failure_rate: 0.0, ttft_ms: 260, state: "CLOSED" },
    { id: "anthropic", name: "Anthropic Claude", status: "CLOSED (HEALTHY)", latency_ms: 310, failure_rate: 0.2, ttft_ms: 410, state: "CLOSED" },
    { id: "ollama", name: "Self-Hosted Ollama (Local vLLM)", status: "CLOSED (HEALTHY)", latency_ms: 12, failure_rate: 0.0, ttft_ms: 25, state: "CLOSED" },
  ]);

  const [thresholds, setThresholds] = useState({
    failure_rate_pct: 5.0,
    ttft_max_ms: 1500,
    cooldown_sec: 30,
    failover_target: "gpt-4o-mini",
  });

  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSaveThresholds = () => {
    setSaving(true);
    setTimeout(() => {
      setSaving(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    }, 600);
  };

  const toggleCircuit = (id) => {
    setProviders(providers.map(p => {
      if (p.id === id) {
        const nextState = p.state === "CLOSED" ? "OPEN" : "CLOSED";
        return {
          ...p,
          state: nextState,
          status: nextState === "OPEN" ? "OPEN (FAILOVER ACTIVE)" : "CLOSED (HEALTHY)",
          failure_rate: nextState === "OPEN" ? 100.0 : 0.0,
        };
      }
      return p;
    }));
  };

  return (
    <AppShell
      title="Circuit Breakers & Failover Governance"
      subtitle="Sub-10ms automated failover, sliding-window latency tracking, and provider health thresholds"
    >
      <div className="space-y-8">
        {/* Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="surface p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-[var(--text-secondary)] mb-2">
              <span className="text-sm font-medium">Failover SLA</span>
              <Zap className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-[var(--text-primary)]">&lt; 10 ms</div>
            <div className="text-xs text-emerald-400 font-medium mt-1">Zero Stream Interruption</div>
          </div>

          <div className="surface p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-[var(--text-secondary)] mb-2">
              <span className="text-sm font-medium">Max TTFT Limit</span>
              <Activity className="w-5 h-5 text-indigo-400" />
            </div>
            <div className="text-2xl font-bold text-[var(--text-primary)]">{thresholds.ttft_max_ms} ms</div>
            <div className="text-xs text-indigo-400 font-medium mt-1">Sliding-Window Latency Cap</div>
          </div>

          <div className="surface p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-[var(--text-secondary)] mb-2">
              <span className="text-sm font-medium">Failure Threshold</span>
              <AlertTriangle className="w-5 h-5 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-[var(--text-primary)]">{thresholds.failure_rate_pct}%</div>
            <div className="text-xs text-amber-400 font-medium mt-1">Auto-Tripping Failure Limit</div>
          </div>

          <div className="surface p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-[var(--text-secondary)] mb-2">
              <span className="text-sm font-medium">Circuit Breaker Engine</span>
              <ShieldCheck className="w-5 h-5 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold text-emerald-400">ACTIVE</div>
            <div className="text-xs text-[var(--text-muted)] mt-1">Rust Data Plane Lock-Free Guard</div>
          </div>
        </div>

        {/* Configuration Sliders */}
        <div className="surface p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] flex items-center gap-2">
                <Sliders className="w-5 h-5 text-indigo-400" />
                Circuit Breaker Threshold Configuration
              </h3>
              <p className="text-sm text-[var(--text-secondary)] mt-1">
                Configure parameters for automatic provider health evaluation and automated failover routing
              </p>
            </div>
            {saveSuccess && (
              <span className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full text-xs font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Thresholds Updated
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2">
                Max Allowed TTFT (Time-To-First-Token): {thresholds.ttft_max_ms} ms
              </label>
              <input
                type="range"
                min="500"
                max="5000"
                step="100"
                value={thresholds.ttft_max_ms}
                onChange={(e) => setThresholds({ ...thresholds, ttft_max_ms: parseInt(e.target.value) })}
                className="w-full h-2 bg-[var(--bg-surface-alt)] rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2">
                Failure Rate Limit: {thresholds.failure_rate_pct}%
              </label>
              <input
                type="range"
                min="1"
                max="25"
                step="0.5"
                value={thresholds.failure_rate_pct}
                onChange={(e) => setThresholds({ ...thresholds, failure_rate_pct: parseFloat(e.target.value) })}
                className="w-full h-2 bg-[var(--bg-surface-alt)] rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2">
                Auto-Recovery Cooldown: {thresholds.cooldown_sec} seconds
              </label>
              <input
                type="range"
                min="10"
                max="120"
                step="5"
                value={thresholds.cooldown_sec}
                onChange={(e) => setThresholds({ ...thresholds, cooldown_sec: parseInt(e.target.value) })}
                className="w-full h-2 bg-[var(--bg-surface-alt)] rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-[var(--border-color)] flex justify-end">
            <button
              onClick={handleSaveThresholds}
              disabled={saving}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium text-xs transition-colors flex items-center gap-2"
            >
              {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5" />}
              Save Circuit Breaker Settings
            </button>
          </div>
        </div>

        {/* Live Provider Matrix */}
        <div className="surface p-6">
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Live Provider Circuit Breaker Status Matrix</h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-[var(--text-primary)]">
              <thead className="bg-[var(--bg-surface-alt)] text-xs uppercase text-[var(--text-secondary)] border-b border-[var(--border-color)]">
                <tr>
                  <th className="p-3">Provider Target</th>
                  <th className="p-3">Avg Latency</th>
                  <th className="p-3">TTFT (P99)</th>
                  <th className="p-3">Failure Rate</th>
                  <th className="p-3">Circuit State</th>
                  <th className="p-3 text-right">Manual Override</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-color)]">
                {providers.map((p) => (
                  <tr key={p.id} className="hover:bg-[var(--bg-surface-alt)]/50 transition-colors">
                    <td className="p-3 font-medium text-[var(--text-primary)] flex items-center gap-2">
                      <Server className="w-4 h-4 text-indigo-400" />
                      {p.name}
                    </td>
                    <td className="p-3 font-mono text-[var(--text-secondary)]">{p.latency_ms} ms</td>
                    <td className="p-3 font-mono text-[var(--text-secondary)]">{p.ttft_ms} ms</td>
                    <td className="p-3 font-mono text-[var(--text-secondary)]">{p.failure_rate}%</td>
                    <td className="p-3">
                      <span
                        className={`px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1.5 w-fit ${
                          p.state === "CLOSED"
                            ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                            : "bg-rose-500/10 text-rose-500 border border-rose-500/20"
                        }`}
                      >
                        {p.state === "CLOSED" ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                        {p.status}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => toggleCircuit(p.id)}
                        className={`px-3 py-1 rounded text-xs font-medium border transition-colors ${
                          p.state === "CLOSED"
                            ? "border-rose-500/30 text-rose-400 hover:bg-rose-500/10"
                            : "border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10"
                        }`}
                      >
                        {p.state === "CLOSED" ? "Trip Circuit Breaker" : "Reset Circuit Breaker"}
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
