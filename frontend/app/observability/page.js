"use client";

import { useEffect, useState } from "react";
import { Activity, Search, RefreshCw, Clock, Play, ShieldAlert, CheckCircle2, HeartPulse } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard } from "../../components/ui";
import { api } from "../../lib/api";

export default function ObservabilityPage() {
  const [metrics, setMetrics] = useState(null);
  const [providerHealth, setProviderHealth] = useState([]);
  const [traces, setTraces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  // Selected Replay & Timeline Modal State
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [replayData, setReplayData] = useState(null);
  const [loadingReplay, setLoadingReplay] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const params = {};
      if (searchQuery) params.query = searchQuery;
      if (statusFilter !== "ALL") params.status = statusFilter;

      const [metricsData, healthData, tracesData] = await Promise.all([
        api.getOperationalMetrics(),
        api.getProviderHealthStatus(),
        api.searchTraces(params),
      ]);

      setMetrics(metricsData);
      setProviderHealth(healthData || []);
      setTraces(tracesData || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadData();
  };

  const handleOpenReplay = async (traceId) => {
    try {
      setLoadingReplay(true);
      const replay = await api.getRequestReplay(traceId);
      setReplayData(replay);
      setSelectedTrace(traceId);
    } catch (err) {
      alert(`Failed to load replay: ${err.message}`);
    } finally {
      setLoadingReplay(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6 max-w-7xl mx-auto">
        <PageTitle
          eyebrow="Control Plane Telemetry"
          title="Enterprise AI Observability & Distributed Traces"
          subtitle="Distributed tracing, execution timeline profiling, live provider health telemetry, and read-only request replay."
          action={
            <Button variant="secondary" size="sm" onClick={loadData}>
              <RefreshCw className="h-3.5 w-3.5" /> Refresh Telemetry
            </Button>
          }
        />

        {loading ? (
          <LoadingCard title="Loading Real-Time Operations Metrics..." />
        ) : error ? (
          <ErrorCard title="Observability Load Error" message={error} onRetry={loadData} />
        ) : (
          <>
            {/* Operational Telemetry Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="surface p-5">
                <div className="flex items-center justify-between text-[var(--text-secondary)] text-xs">
                  <span>Throughput (RPM)</span>
                  <Activity className="h-4 w-4 text-indigo-400" />
                </div>
                <p className="text-2xl font-extrabold text-[var(--text-primary)] mt-2">{metrics?.rpm || 0} req/min</p>
                <p className="text-[11px] text-[var(--text-secondary)] mt-1">Total Traces: {metrics?.total_traces || 0}</p>
              </div>

              <div className="surface p-5">
                <div className="flex items-center justify-between text-[var(--text-secondary)] text-xs">
                  <span>P95 / P99 Latency</span>
                  <Clock className="h-4 w-4 text-cyan-400" />
                </div>
                <p className="text-2xl font-extrabold text-cyan-400 mt-2">{metrics?.p95_latency_ms || 0} ms</p>
                <p className="text-[11px] text-[var(--text-secondary)] mt-1">P99: {metrics?.p99_latency_ms || 0} ms (Avg: {metrics?.avg_latency_ms || 0}ms)</p>
              </div>

              <div className="surface p-5">
                <div className="flex items-center justify-between text-[var(--text-secondary)] text-xs">
                  <span>Error Rate</span>
                  <ShieldAlert className="h-4 w-4 text-rose-400" />
                </div>
                <p className="text-2xl font-extrabold text-rose-400 mt-2">{metrics?.error_rate || 0}%</p>
                <p className="text-[11px] text-[var(--text-secondary)] mt-1">Failures & blocked requests</p>
              </div>

              <div className="surface p-5">
                <div className="flex items-center justify-between text-[var(--text-secondary)] text-xs">
                  <span>Cache Hit Ratio</span>
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                </div>
                <p className="text-2xl font-extrabold text-emerald-400 mt-2">{metrics?.cache_hit_ratio || 0}%</p>
                <p className="text-[11px] text-emerald-400 mt-1">Sub-10ms $0.00 responses</p>
              </div>
            </div>

            {/* Provider Health Telemetry Status Grid */}
            <div className="surface p-6 space-y-4">
              <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                <HeartPulse className="h-4 w-4 text-emerald-400" /> Live LLM Provider Health Telemetry
              </h3>

              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {providerHealth.map((ph) => (
                  <div key={ph.provider_id} className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-3 space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-[var(--text-primary)] uppercase">{ph.provider_name}</span>
                      <Badge variant={ph.status === "HEALTHY" ? "emerald" : ph.status === "DEGRADED" ? "amber" : "rose"}>
                        {ph.status}
                      </Badge>
                    </div>
                    <p className="text-[11px] text-[var(--text-secondary)] font-mono">P95: {ph.p95_latency_ms} ms</p>
                    <p className="text-[11px] text-[var(--text-secondary)] font-mono">Success: {ph.success_rate}%</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Trace Explorer & Search Bar */}
            <div className="space-y-4">
              <form onSubmit={handleSearchSubmit} className="surface p-4 flex flex-wrap gap-3 items-center">
                <div className="relative flex-1 min-w-[200px]">
                  <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search trace ID, prompt text, or model..."
                    className="w-full rounded-xl border border-[var(--border-color)] bg-[var(--input-bg)] py-2 pl-9 pr-4 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)] outline-none focus:border-indigo-500 transition"
                  />
                </div>

                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="rounded-xl border border-[var(--border-color)] bg-[var(--input-bg)] px-3 py-2 text-xs text-[var(--text-primary)] outline-none focus:border-indigo-500 transition"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="SUCCESS">SUCCESS</option>
                  <option value="BLOCKED">BLOCKED</option>
                  <option value="FAILED">FAILED</option>
                </select>

                <Button type="submit" variant="zinc" size="sm">
                  Search Traces
                </Button>
              </form>

              {/* Distributed Trace Explorer Table */}
              <div className="surface overflow-hidden">
                <table className="w-full text-left text-xs text-[var(--text-secondary)]">
                  <thead className="border-b border-[var(--border-color)] bg-[var(--bg-secondary)] uppercase text-[10px] text-[var(--text-muted)] font-bold">
                    <tr>
                      <th className="p-4">Trace ID</th>
                      <th className="p-4">Prompt Snippet</th>
                      <th className="p-4">Provider / Model</th>
                      <th className="p-4">Status</th>
                      <th className="p-4">Latency</th>
                      <th className="p-4">Cost</th>
                      <th className="p-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-color)] font-mono text-[11px]">
                    {traces.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="p-8 text-center text-[var(--text-muted)]">
                          No distributed trace records found.
                        </td>
                      </tr>
                    ) : (
                      traces.map((t) => (
                        <tr key={t.trace_id} className="hover:bg-white/[0.02] transition">
                          <td className="p-4 text-indigo-400 font-bold">{t.trace_id.slice(0, 8)}...</td>
                          <td className="p-4 text-[var(--text-primary)] truncate max-w-[200px]">{t.prompt}</td>
                          <td className="p-4 text-[var(--text-secondary)]">{t.provider_id} / {t.model_id}</td>
                          <td className="p-4">
                            <Badge variant={t.status === "SUCCESS" ? "emerald" : t.status === "BLOCKED" ? "amber" : "rose"}>
                              {t.status}
                            </Badge>
                          </td>
                          <td className="p-4 text-cyan-400 font-bold">{t.total_latency_ms} ms</td>
                          <td className="p-4 text-emerald-400">${t.cost_usd.toFixed(4)}</td>
                          <td className="p-4 text-right">
                            <button
                              onClick={() => handleOpenReplay(t.trace_id)}
                              className="px-2 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 hover:bg-indigo-500/20 rounded-lg flex items-center gap-1 font-sans text-xs ml-auto transition cursor-pointer"
                            >
                              <Play className="h-3 w-3" /> Replay
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {/* Read-Only Request Replay Center & Timeline Viewer Modal */}
        {selectedTrace && replayData && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
            <div className="w-full max-w-3xl rounded-2xl border border-[var(--border-color)] bg-[var(--bg-elevated)] p-6 shadow-2xl space-y-4 max-h-[85vh] flex flex-col">
              <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-3">
                <div>
                  <h3 className="text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                    <Play className="h-4 w-4 text-indigo-400" /> Request Replay Snapshot
                  </h3>
                  <p className="text-xs text-[var(--text-muted)] font-mono">Trace ID: {replayData.trace_id}</p>
                </div>
                <Button variant="zinc" size="sm" onClick={() => setSelectedTrace(null)}>
                  Close
                </Button>
              </div>

              <div className="space-y-4 flex-1 overflow-y-auto pr-1 text-xs">
                {/* Visual Execution Timeline Stages */}
                <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-4 space-y-2">
                  <span className="font-semibold text-[var(--text-primary)] block mb-2">Execution Timeline Profiling:</span>
                  <div className="space-y-1 font-mono text-[11px]">
                    {replayData.timeline_stages?.map((stage, idx) => (
                      <div key={idx} className="flex justify-between items-center p-2 rounded bg-[var(--bg-surface)] border border-[var(--border-color)]">
                        <span className="text-indigo-400 font-bold">{stage.stage_name}</span>
                        <span className="text-cyan-400 font-bold">{stage.duration_ms} ms</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Prompt & Response Details */}
                <div className="space-y-3">
                  <div>
                    <span className="font-semibold text-[var(--text-primary)] block mb-1">Original User Prompt:</span>
                    <div className="rounded-xl border border-[var(--border-color)] bg-[var(--input-bg)] p-3 font-mono text-[11px] text-[var(--text-primary)]">{replayData.prompt}</div>
                  </div>

                  <div>
                    <span className="font-semibold text-[var(--text-primary)] block mb-1">Provider LLM Response:</span>
                    <div className="rounded-xl border border-[var(--border-color)] bg-[var(--input-bg)] p-3 font-mono text-[11px] text-emerald-400 whitespace-pre-wrap">
                      {replayData.response}
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 font-mono text-[11px]">
                    <div className="p-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-surface)]">
                      <span className="text-[var(--text-muted)] block text-[10px]">Total Tokens:</span>
                      <span className="text-[var(--text-primary)] font-bold">{replayData.tokens}</span>
                    </div>
                    <div className="p-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-surface)]">
                      <span className="text-[var(--text-muted)] block text-[10px]">Cost (USD):</span>
                      <span className="text-emerald-400 font-bold">${replayData.cost_usd.toFixed(4)}</span>
                    </div>
                    <div className="p-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-surface)]">
                      <span className="text-[var(--text-muted)] block text-[10px]">Cache Hit:</span>
                      <span className="text-indigo-400 font-bold">{replayData.cache_hit ? "YES" : "NO"}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
