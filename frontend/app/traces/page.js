"use client";

import { useEffect, useState } from "react";
import { Activity, Sparkles, RefreshCw, Search, Clock, Cpu } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, Toast } from "../../components/ui";
import api from "../../lib/api";

export default function ObservabilityTracesPage() {
  const [traces, setTraces] = useState([
    { id: "trace-901", prompt: "Explain quantum computing algorithms", model: "gpt-4o-mini", latency_ms: 240, status: "success", tokens: 512 },
    { id: "trace-902", prompt: "Generate Python async handler", model: "gemini-2.0-flash", latency_ms: 180, status: "success", tokens: 320 },
    { id: "trace-903", prompt: "Analyze customer sentiment dataset", model: "tinyllama", latency_ms: 95, status: "success", tokens: 180 },
  ]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState("");

  const refreshTraces = async () => {
    setLoading(true);
    try {
      if (api.searchTraces) {
        const res = await api.searchTraces();
        if (res && res.length > 0) setTraces(res);
      }
      setToast("Observability traces refreshed.");
    } catch (e) {
      console.warn("Traces fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell
      title="Observability & Spans"
      subtitle="Real-time LLM telemetry, request traces, latency spans, and execution diagnostics"
    >
      <PageTitle
        eyebrow="Runtime Telemetry"
        title="Observability & Spans"
        subtitle="Inspect real-time gateway traces, model execution latencies, and token usage across requests."
        action={
          <Button onClick={refreshTraces} variant="secondary" className="text-xs">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh Traces
          </Button>
        }
      />

      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="surface p-4 border border-[var(--border-color)] rounded-xl">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400">
                <Activity className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">99.98%</p>
                <p className="text-xs text-slate-400">Trace Success SLA</p>
              </div>
            </div>
          </div>

          <div className="surface p-4 border border-[var(--border-color)] rounded-xl">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-sky-500/10 text-sky-400">
                <Clock className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">172ms</p>
                <p className="text-xs text-slate-400">Avg Span Latency</p>
              </div>
            </div>
          </div>

          <div className="surface p-4 border border-[var(--border-color)] rounded-xl">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-purple-500/10 text-purple-400">
                <Cpu className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">1.012k</p>
                <p className="text-xs text-slate-400">Tokens Processed</p>
              </div>
            </div>
          </div>
        </div>

        <div className="surface p-6 border border-[var(--border-color)] rounded-2xl space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Live Execution Traces</h3>

          <div className="divide-y divide-white/10">
            {traces.map((t) => (
              <div key={t.id} className="py-3.5 flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-white font-mono">{t.id} - "{t.prompt}"</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">Model: {t.model} | Tokens: {t.tokens}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    {t.latency_ms}ms
                  </span>
                  <Badge tone="green">{t.status}</Badge>
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
