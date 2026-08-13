"use client";

import { useEffect, useState } from "react";
import { Database, Zap, DollarSign, Clock, RefreshCw, Trash2, CheckCircle2, Flame } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import { api } from "../../lib/api";

export default function CachePage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await api.getCacheStats();
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

  const handleInvalidateCache = async () => {
    if (!confirm("Are you sure you want to invalidate all semantic cache entries?")) return;
    try {
      const res = await api.invalidateCache();
      setToast({ type: "success", message: `Cache invalidated! Removed ${res.invalidated_count} entries.` });
      loadStats();
    } catch (err) {
      setToast({ type: "error", message: `Failed: ${err.message}` });
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageTitle
          title="Enterprise Semantic Cache Analytics"
          subtitle="Real-time prompt-response cache hit telemetry, cost savings, and latency reduction metrics."
          action={
            <div className="flex gap-2">
              <Button variant="zinc" onClick={loadStats}>
                <RefreshCw className="h-4 w-4" /> Refresh
              </Button>
              <Button variant="danger" onClick={handleInvalidateCache}>
                <Trash2 className="h-4 w-4" /> Clear Cache
              </Button>
            </div>
          }
        />

        {toast && <Toast type={toast.type} message={toast.message} onClose={() => setToast(null)} />}

        {loading ? (
          <LoadingCard title="Loading Cache Metrics..." />
        ) : error ? (
          <ErrorCard title="Cache Load Error" message={error} onRetry={loadStats} />
        ) : (
          <>
            {/* Top Stat Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl">
                <div className="flex items-center justify-between text-slate-400 text-xs">
                  <span>Cache Hit Rate</span>
                  <Zap className="h-4 w-4 text-emerald-400" />
                </div>
                <p className="text-2xl font-extrabold text-white mt-2">{stats?.hit_rate_pct ?? 0}%</p>
                <p className="text-[11px] text-emerald-400 mt-1">
                  {stats?.total_hits || 0} total hits ({stats?.exact_hits || 0} exact, {stats?.semantic_hits || 0} semantic)
                </p>
              </div>

              <div className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl">
                <div className="flex items-center justify-between text-slate-400 text-xs">
                  <span>AI Cost Saved</span>
                  <DollarSign className="h-4 w-4 text-emerald-400" />
                </div>
                <p className="text-2xl font-extrabold text-emerald-400 mt-2">${(stats?.total_cost_saved_usd || 0).toFixed(4)}</p>
                <p className="text-[11px] text-slate-400 mt-1">Direct LLM API cost elimination</p>
              </div>

              <div className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl">
                <div className="flex items-center justify-between text-slate-400 text-xs">
                  <span>Avg Latency Saved</span>
                  <Clock className="h-4 w-4 text-indigo-400" />
                </div>
                <p className="text-2xl font-extrabold text-indigo-300 mt-2">{stats?.avg_latency_saved_ms || 0} ms</p>
                <p className="text-[11px] text-indigo-400 mt-1">Sub-10ms cache retrieval speed</p>
              </div>

              <div className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl">
                <div className="flex items-center justify-between text-slate-400 text-xs">
                  <span>Active Cache Entries</span>
                  <Database className="h-4 w-4 text-amber-400" />
                </div>
                <p className="text-2xl font-extrabold text-amber-300 mt-2">{stats?.active_entries || 0}</p>
                <p className="text-[11px] text-slate-400 mt-1">In-memory SHA-256 / similarity index</p>
              </div>
            </div>

            {/* Comprehensive Metrics Breakdown */}
            <div className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" /> Cache Telemetry Breakdown
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-xs">
                <div className="rounded-xl border border-white/10 bg-black/30 p-4">
                  <span className="text-slate-400 block">Total Ingested Requests</span>
                  <span className="text-base font-bold text-white mt-1 block">{stats?.total_requests || 0}</span>
                </div>

                <div className="rounded-xl border border-white/10 bg-black/30 p-4">
                  <span className="text-slate-400 block">Total Tokens Saved</span>
                  <span className="text-base font-bold text-emerald-300 mt-1 block">{(stats?.total_tokens_saved || 0).toLocaleString()} tokens</span>
                </div>

                <div className="rounded-xl border border-white/10 bg-black/30 p-4">
                  <span className="text-slate-400 block">Total Evictions / Invalidations</span>
                  <span className="text-base font-bold text-amber-300 mt-1 block">{(stats?.evictions || 0) + (stats?.invalidations || 0)}</span>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
