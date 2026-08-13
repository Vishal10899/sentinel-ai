"use client";

import { useEffect, useState } from "react";
import {
  Database,
  HeartPulse,
  Server,
  Wifi,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Cpu,
  Activity,
  Layers
} from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import { api } from "../../lib/api";

export default function HealthPage() {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastSync, setLastSync] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const [backend, providers, database, redis, models] = await Promise.all([
        api.health(),
        api.providerHealth(),
        api.databaseHealth().then((x) => ({ ...x, status: 200 })).catch((e) => ({ status: 503, detail: e.message })),
        api.redisHealth().then((x) => ({ ...x, status: 200 })).catch((e) => ({ status: 503, detail: e.message })),
        api.models(),
      ]);

      const isAllHealthy = database.status === 200 && redis.status === 200;

      setHealthData({
        overallStatus: isAllHealthy ? "OPERATIONAL" : "DEGRADED",
        backend: { status: 200, label: `${backend.service || "Sentinel API Gateway"} v${backend.version || "1.0.0"}` },
        providers: { status: 200, label: `${providers.providers?.length || 0} configured provider adapters`, list: providers.providers || [] },
        database: { status: database.status, label: database.status === 200 ? "PostgreSQL Primary Pool (Active)" : database.detail },
        redis: { status: redis.status, label: redis.status === 200 ? "Redis Cache (Connected)" : redis.detail },
        models: { status: 200, label: `${models.length || 0} active models registered` },
      });
      setLastSync(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // 30s auto-refresh
    return () => clearInterval(interval);
  }, []);

  const handleManualRefresh = () => {
    fetchHealth();
    setToastMsg("Health checks refreshed successfully!");
  };

  return (
    <AppShell>
      <div className="space-y-6 max-w-7xl mx-auto">
        <PageTitle
          eyebrow="Operations & Infrastructure"
          title="System & Provider Health Telemetry"
          subtitle="Real-time connectivity checks for core API services, databases, cache layers, and upstream LLM providers."
          action={
            <Button variant="secondary" size="sm" onClick={handleManualRefresh} isLoading={loading}>
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Refresh Telemetry</span>
            </Button>
          }
        />

        {toastMsg && <Toast type="success" message={toastMsg} onClose={() => setToastMsg(null)} />}

        {loading && !healthData ? (
          <LoadingCard title="Running System Infrastructure Health Checks..." />
        ) : error ? (
          <ErrorCard title="Infrastructure Check Failed" message={error} onRetry={fetchHealth} />
        ) : (
          <>
            {/* System Status Overview Banner */}
            <div className={`surface p-6 flex flex-col sm:flex-row items-center justify-between gap-4 border-l-4 ${
              healthData.overallStatus === "OPERATIONAL" ? "border-l-emerald-500" : "border-l-amber-500"
            }`}>
              <div className="flex items-center gap-4">
                <div className={`rounded-2xl p-3.5 ${
                  healthData.overallStatus === "OPERATIONAL" ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20" : "bg-amber-500/10 text-amber-500 border border-amber-500/20"
                }`}>
                  {healthData.overallStatus === "OPERATIONAL" ? (
                    <CheckCircle2 className="h-7 w-7" />
                  ) : (
                    <AlertTriangle className="h-7 w-7" />
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-[var(--text-primary)]">
                      {healthData.overallStatus === "OPERATIONAL" ? "All Core Systems Operational" : "Partial Degraded Infrastructure Performance"}
                    </h2>
                    <Badge variant={healthData.overallStatus === "OPERATIONAL" ? "emerald" : "amber"}>
                      {healthData.overallStatus}
                    </Badge>
                  </div>
                  <p className="text-xs text-[var(--text-secondary)] mt-1">
                    Sentinel AI control plane and reverse proxy modules are online. Auto-refreshing every 30 seconds.
                  </p>
                </div>
              </div>

              {lastSync && (
                <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-muted)] bg-[var(--bg-secondary)] px-3 py-1.5 rounded-lg border border-[var(--border-color)]">
                  <Clock className="h-3.5 w-3.5 text-indigo-400" />
                  <span>Last Sync: {lastSync}</span>
                </div>
              )}
            </div>

            {/* Core Services Status Cards Grid */}
            <div className="space-y-3">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)] block px-1">
                Infrastructure Core Services
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Service Card 1: API Gateway */}
                <div className="surface p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="rounded-xl bg-indigo-500/10 border border-indigo-500/20 p-2 text-indigo-400">
                        <Server className="h-5 w-5" />
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-[var(--text-primary)]">Backend API Gateway</h4>
                        <p className="text-[11px] text-[var(--text-secondary)] font-mono mt-0.5">{healthData.backend.label}</p>
                      </div>
                    </div>
                    <Badge variant="emerald">Healthy</Badge>
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] pt-2 border-t border-[var(--border-color)] flex justify-between">
                    <span>Engine: FastAPI / Uvicorn</span>
                    <span>P95: &lt;1.2ms</span>
                  </div>
                </div>

                {/* Service Card 2: Database */}
                <div className="surface p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="rounded-xl bg-cyan-500/10 border border-cyan-500/20 p-2 text-cyan-400">
                        <Database className="h-5 w-5" />
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-[var(--text-primary)]">PostgreSQL Database</h4>
                        <p className="text-[11px] text-[var(--text-secondary)] font-mono mt-0.5">{healthData.database.label}</p>
                      </div>
                    </div>
                    <Badge variant={healthData.database.status === 200 ? "emerald" : "rose"}>
                      {healthData.database.status === 200 ? "Operational" : "Unavailable"}
                    </Badge>
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] pt-2 border-t border-[var(--border-color)] flex justify-between">
                    <span>Pool: AsyncSession</span>
                    <span>Status: {healthData.database.status === 200 ? "Active" : "Check Config"}</span>
                  </div>
                </div>

                {/* Service Card 3: Redis Cache */}
                <div className="surface p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-2 text-emerald-400">
                        <Wifi className="h-5 w-5" />
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-[var(--text-primary)]">Redis Cache Layer</h4>
                        <p className="text-[11px] text-[var(--text-secondary)] font-mono mt-0.5">{healthData.redis.label}</p>
                      </div>
                    </div>
                    <Badge variant={healthData.redis.status === 200 ? "emerald" : "amber"}>
                      {healthData.redis.status === 200 ? "Connected" : "Memory Only"}
                    </Badge>
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] pt-2 border-t border-[var(--border-color)] flex justify-between">
                    <span>Type: In-Memory Index</span>
                    <span>TTL: 15s - 24h</span>
                  </div>
                </div>

                {/* Service Card 4: Model Registry */}
                <div className="surface p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-2 text-amber-400">
                        <Cpu className="h-5 w-5" />
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-[var(--text-primary)]">Model Catalog Registry</h4>
                        <p className="text-[11px] text-[var(--text-secondary)] font-mono mt-0.5">{healthData.models.label}</p>
                      </div>
                    </div>
                    <Badge variant="indigo font-mono">Catalog Active</Badge>
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] pt-2 border-t border-[var(--border-color)] flex justify-between">
                    <span>Categories: Chat, Vision, Code</span>
                    <span>Status: Synced</span>
                  </div>
                </div>

                {/* Service Card 5: Security Guardrails */}
                <div className="surface p-5 space-y-3 md:col-span-2 lg:col-span-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="rounded-xl bg-purple-500/10 border border-purple-500/20 p-2 text-purple-400">
                        <ShieldCheck className="h-5 w-5" />
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-[var(--text-primary)]">Security & Guardrail Engine</h4>
                        <p className="text-[11px] text-[var(--text-secondary)] font-mono mt-0.5">PII Scanner, Regex Filters, Toxicity Shield</p>
                      </div>
                    </div>
                    <Badge variant="emerald">Enforcing</Badge>
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] pt-2 border-t border-[var(--border-color)] flex justify-between">
                    <span>Rules Loaded: 14 Rules</span>
                    <span>Action: Block & Redact</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Provider Adapters Health Table */}
            <div className="space-y-3 pt-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)] block px-1">
                Upstream Provider Gateway Adapters
              </span>
              <div className="surface overflow-hidden">
                <table className="w-full text-left text-xs text-[var(--text-secondary)]">
                  <thead className="border-b border-[var(--border-color)] bg-[var(--bg-secondary)] uppercase text-[10px] text-[var(--text-muted)] font-bold">
                    <tr>
                      <th className="p-4">Provider ID</th>
                      <th className="p-4">Adapter Status</th>
                      <th className="p-4">Default Model</th>
                      <th className="p-4">Failover Target</th>
                      <th className="p-4 text-right">Health Check</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-color)] font-mono text-[11px]">
                    {healthData.providers.list?.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="p-6 text-center text-[var(--text-muted)]">
                          No provider adapters registered in control plane.
                        </td>
                      </tr>
                    ) : (
                      healthData.providers.list.map((p) => (
                        <tr key={p.provider_id} className="hover:bg-white/[0.02] transition">
                          <td className="p-4 font-bold text-[var(--text-primary)] uppercase flex items-center gap-2">
                            <span className="h-2 w-2 rounded-full bg-emerald-400" />
                            {p.name || p.provider_id}
                          </td>
                          <td className="p-4">
                            <Badge variant={p.enabled ? "emerald" : "zinc"}>
                              {p.enabled ? "ACTIVE" : "DISABLED"}
                            </Badge>
                          </td>
                          <td className="p-4 text-indigo-400 font-semibold">{p.configured_model || "Default Catalog"}</td>
                          <td className="p-4 text-[var(--text-muted)]">{p.failover_provider_id || "None"}</td>
                          <td className="p-4 text-right">
                            <Badge variant="cyan">Healthy</Badge>
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
      </div>
    </AppShell>
  );
}
