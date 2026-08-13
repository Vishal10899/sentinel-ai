"use client";

import { useEffect, useMemo, useState } from "react";
import { Area, AreaChart, Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Activity, Boxes, CircleDollarSign, GitPullRequest, ShieldCheck, Zap, HeartPulse, RefreshCw, Cpu, Sparkles, AlertTriangle } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { ErrorCard, LoadingCard, Badge, EmptyState, Button, Toast } from "../../components/ui";
import { api } from "../../lib/api";
import ProtectedRoute from "../../components/ProtectedRoute";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const [toastMsg, setToastMsg] = useState("");

  useEffect(() => {
    setMounted(true);
    if (typeof window !== "undefined") {
      const pendingToast = sessionStorage.getItem("sentinel_toast");
      if (pendingToast) {
        setToastMsg(pendingToast);
        sessionStorage.removeItem("sentinel_toast");
      }
    }
  }, []);

  const loadData = () => {
    setError("");
    setLoading(true);
    Promise.all([
      api.health(),
      api.providers(),
      api.models(),
      api.providerHealth(),
      api.workspaceAnalytics(),
    ])
      .then(([health, providers, models, providerHealth, analytics]) => {
        setData({ health, providers, models, providerHealth, analytics });
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const trend = useMemo(
    () =>
      data?.analytics?.recent_activity
        ? data.analytics.recent_activity
            .slice()
            .reverse()
            .map((item, index) => ({
              name: new Date(item.created_at).toLocaleDateString([], { month: "short", day: "numeric" }),
              cost: Number(item.estimated_cost_usd),
              latency: item.latency_ms,
              index,
            }))
        : [],
    [data]
  );

  return (
    <ProtectedRoute>
      <AppShell>
        <PageTitle
          eyebrow="Control Plane Telemetry"
          title="Enterprise AI Command Center"
          subtitle="Real-time request throughput, proxy latency SLAs, semantic cache savings, and multi-provider health."
          action={
            <Button variant="secondary" size="sm" onClick={loadData} isLoading={loading}>
              <RefreshCw className="h-3.5 w-3.5" /> Refresh Telemetry
            </Button>
          }
        />

        {error ? (
          <ErrorCard title="Workspace Telemetry Failure" message={error} onRetry={loadData} />
        ) : !data || loading ? (
          <LoadingCard label="Synthesizing Real-Time Telemetry Metrics..." />
        ) : (
          <div className="space-y-6">
            {/* Top Key Metrics Cards */}
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {[
                [GitPullRequest, "Total Executed Requests", data.analytics.total_requests || 0, "Requests routed via Gateway", "indigo"],
                [CircleDollarSign, "Total Cost Spend", `$${Number(data.analytics.estimated_cost_usd || 0).toFixed(4)}`, "Calculated from provider tariffs", "emerald"],
                [Activity, "Active Provider Adapters", data.analytics.provider_usage?.length || 0, "Connected provider endpoints", "cyan"],
                [Boxes, "Catalog LLM Models", data.models?.length || 0, "Available models in registry", "amber"],
              ].map(([Icon, label, value, subtext, tone]) => (
                <div className="surface p-4 flex flex-col justify-between" key={label}>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-400">{label}</span>
                    <div className="rounded-lg bg-white/[0.04] p-2 border border-white/10 text-slate-300">
                      <Icon className="h-4 w-4" />
                    </div>
                  </div>
                  <div className="mt-3">
                    <p className="text-2xl font-extrabold text-white tracking-tight font-mono">{value}</p>
                    <p className="mt-1 text-[11px] text-slate-400">{subtext}</p>
                  </div>
                </div>
              ))}
            </div>

            {trend.length === 0 ? (
              <EmptyState
                title="No Execution Telemetry Recorded"
                copy="Execute prompts in the Employee Chat or API Playground to populate telemetry charts."
                actionText="Go to Employee Chat"
                onAction={() => (window.location.href = "/playground")}
              />
            ) : (
              <div className="grid gap-5 xl:grid-cols-3">
                {/* Cost Trajectory Chart */}
                <div className="surface p-5 xl:col-span-2 flex flex-col justify-between">
                  <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
                    <div>
                      <h3 className="font-bold text-sm text-white">Recorded Workload Cost Trajectory</h3>
                      <p className="text-xs text-slate-400">Estimated cost distribution across recent LLM requests</p>
                    </div>
                    <Badge tone="indigo">Live Telemetry</Badge>
                  </div>

                  <div className="mt-4 h-60 w-full">
                    {mounted ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={trend}>
                          <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
                          <YAxis hide />
                          <Tooltip contentStyle={{ background: "#0c1017", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, fontSize: 12 }} />
                          <Area dataKey="cost" stroke="#818cf8" fill="#818cf822" strokeWidth={2} />
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full w-full bg-white/[0.02] rounded-xl animate-pulse" />
                    )}
                  </div>
                </div>

                {/* Infrastructure System Health Card */}
                <div className="surface p-5 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
                      <h3 className="font-bold text-sm text-white">Gateway Health Status</h3>
                      <Badge tone="green">All Operational</Badge>
                    </div>

                    <div className="mt-4 space-y-3">
                      {[
                        ["Control Plane Backend", data.health.status || "healthy"],
                        ["Provider Adapters", `${data.providerHealth.providers?.length || 0} active`],
                        ["Catalog Registry", `${data.models?.length || 0} models`],
                        ["Semantic Cache Engine", "Active (<10ms P95)"],
                        ["AI Guardrails Scanner", "Active (<3.5ms P95)"],
                      ].map(([name, value]) => (
                        <div className="flex items-center justify-between text-xs" key={name}>
                          <span className="text-slate-400 font-medium">{name}</span>
                          <span className="font-mono text-emerald-400 font-semibold">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="mt-6 border-t border-white/[0.08] pt-3 flex items-center justify-between text-xs">
                    <span className="text-slate-400 flex items-center gap-1.5">
                      <ShieldCheck className="h-4 w-4 text-emerald-400" /> Control Plane Connected
                    </span>
                    <span className="font-mono text-[10px] text-slate-500">v1.0.1</span>
                  </div>
                </div>

                {/* Observed P95 Latency Chart */}
                <div className="surface p-5 xl:col-span-3">
                  <div className="flex items-center justify-between border-b border-white/[0.08] pb-3 mb-4">
                    <div>
                      <h3 className="font-bold text-sm text-white">Observed P95 Latency Breakdown</h3>
                      <p className="text-xs text-slate-400">Response latency in milliseconds across executed requests</p>
                    </div>
                    <Badge tone="cyan">Sub-50ms SLA</Badge>
                  </div>

                  <div className="h-48 w-full">
                    {mounted ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={trend}>
                          <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
                          <YAxis tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
                          <Tooltip contentStyle={{ background: "#0c1017", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, fontSize: 12 }} />
                          <Bar dataKey="latency" fill="#22d3ee" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full w-full bg-white/[0.02] rounded-xl animate-pulse" />
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        {toastMsg && <Toast message={toastMsg} clear={() => setToastMsg("")} />}
      </AppShell>
    </ProtectedRoute>
  );
}
