"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Cable,
  FlaskConical,
  Power,
  Search,
  Plus,
  RefreshCw,
  SlidersHorizontal,
  Activity,
  ShieldCheck,
  Zap,
  Clock,
  Eye,
  Mic,
  Code2,
  Lock,
  Layers,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  X,
  ChevronRight,
  Settings2,
  Shuffle,
} from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import { api } from "../../lib/api";
import WithAdminAuth from "../../components/WithAdminAuth";


function ProvidersPage() {
  const [providers, setProviders] = useState(null);
  const [models, setModels] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [toast, setToast] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState("priority");

  // Modals & Drawer State
  const [configModal, setConfigModal] = useState(null); // Provider object to configure
  const [addModal, setAddModal] = useState(false); // Add new provider modal
  const [drawerProvider, setDrawerProvider] = useState(null); // Detailed inspect drawer

  // Form State for Editing/Adding
  const [formState, setFormState] = useState({});

  const loadData = () => {
    setError("");
    Promise.all([api.providers(), api.models()])
      .then(([provList, modelList]) => {
        setProviders(provList);
        setModels(modelList || []);
      })
      .catch((e) => setError(e.message));
  };

  useEffect(loadData, []);

  // Compute KPI Dashboard stats
  const stats = useMemo(() => {
    if (!providers || providers.length === 0)
      return { total: 0, healthy: 0, degraded: 0, avgLatency: 0, failoverCount: 0 };
    const healthyCount = providers.filter(
      (p) => p.status === "healthy" || p.status === "configured"
    ).length;
    const degradedCount = providers.filter(
      (p) => p.status === "degraded" || p.status === "unhealthy"
    ).length;
    const latencies = providers.map((p) => p.last_latency_ms || 0).filter((l) => l > 0);
    const avgLat =
      latencies.length > 0
        ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length)
        : 0;
    const failoverActive = providers.filter((p) => p.auto_failover).length;
    return {
      total: providers.length,
      healthy: healthyCount,
      degraded: degradedCount,
      avgLatency: avgLat,
      failoverCount: failoverActive,
    };
  }, [providers]);

  // Filtered & Sorted Provider List
  const filteredProviders = useMemo(() => {
    if (!providers) return [];
    let list = providers.filter((p) => {
      const matchSearch = `${p.provider_name} ${p.provider_id} ${p.configured_model || ""}`
        .toLowerCase()
        .includes(search.toLowerCase());
      const matchStatus =
        statusFilter === "all" ||
        (statusFilter === "healthy" && (p.status === "healthy" || p.status === "configured")) ||
        p.status === statusFilter;
      return matchSearch && matchStatus;
    });

    return list.sort((a, b) => {
      if (sortBy === "latency") return (a.last_latency_ms || 0) - (b.last_latency_ms || 0);
      if (sortBy === "failures") return (b.failure_count || 0) - (a.failure_count || 0);
      if (sortBy === "name") return a.provider_name.localeCompare(b.provider_name);
      return (a.priority || 10) - (b.priority || 10);
    });
  }, [providers, search, statusFilter, sortBy]);

  // Actions
  const handleToggle = async (prov) => {
    setBusy(prov.provider_id);
    try {
      const res = await api.toggleProvider(prov.provider_id, !prov.enabled);
      setToast(`${prov.provider_name} is now ${res.enabled ? "enabled" : "disabled"}`);
      loadData();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy("");
    }
  };

  const handleTest = async (prov) => {
    setBusy(prov.provider_id);
    try {
      const res = await api.testProvider(prov.provider_id);
      setToast(
        `${prov.provider_name}: ${res.valid ? "Healthy" : "Failed"} (${res.latency_ms}ms) - ${res.message}`
      );
      loadData();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy("");
    }
  };

  const handleHealthCheck = async (prov) => {
    setBusy(prov.provider_id);
    try {
      const res = await api.healthCheckProvider(prov.provider_id);
      setToast(`${prov.provider_name} health updated: ${res.status}`);
      loadData();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy("");
    }
  };

  const openConfigModal = (prov) => {
    setConfigModal(prov);
    setFormState({
      api_key: "",
      model: prov.configured_model || "",
      base_url: prov.base_url || "",
      organization_id: prov.organization_id || "",
      timeout_seconds: prov.timeout_seconds || 30,
      retry_count: prov.retry_count || 3,
      rate_limit_rpm: prov.rate_limit_rpm || 600,
      rate_limit_tpm: prov.rate_limit_tpm || 100000,
      priority: prov.priority || 10,
      cost_multiplier: prov.cost_multiplier || 1.0,
      primary_provider_id: prov.primary_provider_id || "",
      secondary_provider_id: prov.secondary_provider_id || "",
      auto_failover: prov.auto_failover ?? true,
      supports_streaming: prov.supports_streaming ?? true,
      supports_vision: prov.supports_vision ?? false,
      supports_audio: prov.supports_audio ?? false,
      supports_function_calling: prov.supports_function_calling ?? true,
    });
  };

  const saveConfiguration = async (updatedPayload) => {
    if (!configModal) return;
    setBusy(configModal.provider_id);
    try {
      const payload = updatedPayload || { ...formState };
      if (!payload.api_key || !payload.api_key.trim()) delete payload.api_key;
      await api.configureProvider(configModal.provider_id, payload);
      setToast(`${configModal.provider_name} settings updated successfully`);
      setConfigModal(null);
      loadData();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy("");
    }
  };


  const handleCreateProvider = async () => {
    if (!formState.provider_id || !formState.provider_name) {
      setError("Provider ID and Name are required.");
      return;
    }
    setBusy("create");
    try {
      await api.createProvider(formState);
      setToast(`Provider ${formState.provider_name} created successfully`);
      setAddModal(false);
      loadData();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy("");
    }
  };

  const handleDeleteProvider = async (provId) => {
    if (!confirm(`Are you sure you want to delete provider '${provId}'?`)) return;
    setBusy(provId);
    try {
      await api.deleteProvider(provId);
      setToast(`Provider ${provId} deleted`);
      if (drawerProvider?.provider_id === provId) setDrawerProvider(null);
      loadData();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy("");
    }
  };

  return (
    <AppShell
      title="Enterprise Provider Management"
      subtitle="Central control plane for vendor adapters, health checks, & resilience"
    >
      <PageTitle
        eyebrow="Infrastructure & Resilience"
        title="AI Provider Control Plane"
        copy="Configure API credentials, inspect real-time latency SLAs, manage rate limits, and set up automatic failover chains across LLM providers."
        action={
          <Button onClick={() => {
            setFormState({
              provider_id: "",
              provider_name: "",
              api_key: "",
              base_url: "",
              default_model: "",
              priority: 10,
              cost_multiplier: 1.0,
            });
            setAddModal(true);
          }}>
            <Plus className="h-4 w-4" /> Add Provider
          </Button>
        }
      />

      {error ? (
        <ErrorCard error={error} retry={loadData} />
      ) : !providers ? (
        <LoadingCard label="Loading Provider Management Control Plane..." />
      ) : (
        <>
          {/* KPI Dashboard Cards */}
          <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-5">
            <div className="surface p-4 flex items-center gap-3">
              <div className="rounded-xl bg-indigo-500/10 p-3 text-indigo-400">
                <Cable className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.total}</p>
                <p className="text-xs text-slate-400">Total Providers</p>
              </div>
            </div>

            <div className="surface p-4 flex items-center gap-3">
              <div className="rounded-xl bg-emerald-500/10 p-3 text-emerald-400">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.healthy}</p>
                <p className="text-xs text-slate-400">Healthy & Active</p>
              </div>
            </div>

            <div className="surface p-4 flex items-center gap-3">
              <div className="rounded-xl bg-amber-500/10 p-3 text-amber-400">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.degraded}</p>
                <p className="text-xs text-slate-400">Degraded / Issues</p>
              </div>
            </div>

            <div className="surface p-4 flex items-center gap-3">
              <div className="rounded-xl bg-sky-500/10 p-3 text-sky-400">
                <Clock className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.avgLatency}ms</p>
                <p className="text-xs text-slate-400">Avg Latency SLA</p>
              </div>
            </div>

            <div className="surface p-4 flex items-center gap-3 col-span-2 lg:col-span-1">
              <div className="rounded-xl bg-purple-500/10 p-3 text-purple-400">
                <Shuffle className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.failoverCount}</p>
                <p className="text-xs text-slate-400">Auto-Failover Active</p>
              </div>
            </div>
          </div>

          {/* Search, Filter, & Sort Bar */}
          <div className="surface mb-6 p-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by provider name, ID, or model..."
                className="w-full rounded-xl bg-black/30 py-2.5 pl-9 pr-4 text-sm text-white outline-none border border-white/10 focus:border-indigo-500/50"
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="rounded-xl border border-white/10 bg-[#121827] px-3 py-2 text-xs text-slate-300 outline-none"
              >
                <option value="all">All Statuses</option>
                <option value="healthy">Healthy / Configured</option>
                <option value="degraded">Degraded</option>
                <option value="unhealthy">Unhealthy</option>
                <option value="unconfigured">Unconfigured</option>
              </select>

              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="rounded-xl border border-white/10 bg-[#121827] px-3 py-2 text-xs text-indigo-300 outline-none"
              >
                <option value="priority">Sort: Priority Rank</option>
                <option value="latency">Sort: Latency SLA</option>
                <option value="failures">Sort: Failure Count</option>
                <option value="name">Sort: Provider Name</option>
              </select>

              <Button
                variant="secondary"
                onClick={loadData}
                className="py-2 text-xs"
              >
                <RefreshCw className="h-3.5 w-3.5" /> Refresh
              </Button>
            </div>
          </div>

          {/* Provider Grid Cards */}
          {filteredProviders.length === 0 ? (
            <EmptyState
              title="No providers found"
              copy="Add a new provider or adjust search filters."
            />
          ) : (
            <div className="grid gap-5 md:grid-cols-2">
              {filteredProviders.map((prov) => {
                const isBusy = busy === prov.provider_id;
                const supportedModels = models.filter(
                  (m) => m.provider_id === prov.provider_id
                );
                const theme = PROVIDER_THEMES[prov.provider_id] || {
                  bg: "bg-slate-500/10",
                  border: "border-slate-500/20",
                  text: "text-slate-300",
                  label: prov.provider_name,
                };

                const statusTone =
                  prov.status === "healthy" || prov.status === "configured"
                    ? "green"
                    : prov.status === "degraded"
                    ? "amber"
                    : prov.status === "unhealthy"
                    ? "red"
                    : "slate";

                return (
                  <article
                    key={prov.provider_id}
                    className="surface p-6 flex flex-col justify-between"
                  >
                    <div>
                      {/* Card Header */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`grid h-11 w-11 place-items-center rounded-xl border ${theme.bg} ${theme.border}`}>
                            <Cable className={`h-5 w-5 ${theme.text}`} />
                          </div>
                          <div>
                            <h3 className="text-lg font-bold text-white">
                              {prov.provider_name}
                            </h3>
                            <p className="font-mono text-xs text-slate-400">
                              {prov.provider_id}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <Badge tone={statusTone}>
                            {prov.status || "unconfigured"}
                          </Badge>
                        </div>
                      </div>

                      {/* Configured Model & Key info */}
                      <div className="mt-4 rounded-xl bg-black/20 p-3 flex justify-between items-center text-xs">
                        <div>
                          <p className="text-slate-400">Default Model</p>
                          <p className="mt-0.5 font-semibold text-slate-200">
                            {prov.configured_model || "Not set"}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-slate-400">API Credentials</p>
                          <p className="mt-0.5 font-mono text-slate-300">
                            {prov.api_key_masked || "No key provided"}
                          </p>
                        </div>
                      </div>

                      {/* Performance & Failover Stats */}
                      <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
                        <div className="rounded-lg bg-white/[0.03] p-2">
                          <p className="text-slate-400 text-[10px]">Latency</p>
                          <p className="font-semibold text-emerald-400">
                            {prov.last_latency_ms ? `${prov.last_latency_ms}ms` : "--"}
                          </p>
                        </div>
                        <div className="rounded-lg bg-white/[0.03] p-2">
                          <p className="text-slate-400 text-[10px]">Priority / Cost</p>
                          <p className="font-semibold text-sky-400">
                            P{prov.priority || 10} · {prov.cost_multiplier || 1.0}x
                          </p>
                        </div>
                        <div className="rounded-lg bg-white/[0.03] p-2">
                          <p className="text-slate-400 text-[10px]">Failures</p>
                          <p className={`font-semibold ${prov.consecutive_failures > 0 ? "text-rose-400" : "text-slate-300"}`}>
                            {prov.consecutive_failures || 0}
                          </p>
                        </div>
                      </div>

                      {/* Supported Models list */}
                      <div className="mt-4 pt-3 border-t border-white/[0.06]">
                        <p className="text-xs text-slate-400 mb-1.5 flex justify-between">
                          <span>Supported Models in Registry</span>
                          <span className="font-semibold text-white">{supportedModels.length}</span>
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {supportedModels.slice(0, 4).map((m) => (
                            <span
                              key={m.model_id}
                              className="rounded bg-white/[0.05] px-2 py-0.5 text-[11px] text-slate-300"
                            >
                              {m.display_name}
                            </span>
                          ))}
                          {supportedModels.length > 4 && (
                            <span className="rounded bg-white/[0.05] px-2 py-0.5 text-[11px] text-indigo-300">
                              +{supportedModels.length - 4} more
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Quick Action Controls */}
                    <div className="mt-5 flex flex-wrap items-center justify-between gap-2 pt-4 border-t border-white/[0.06]">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="secondary"
                          size="sm"
                          disabled={isBusy}
                          onClick={() => handleTest(prov)}
                          className="py-1.5 text-xs"
                        >
                          <FlaskConical className="h-3.5 w-3.5" /> Test
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          disabled={isBusy}
                          onClick={() => openConfigModal(prov)}
                          className="py-1.5 text-xs"
                        >
                          <Settings2 className="h-3.5 w-3.5" /> Config
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDrawerProvider(prov)}
                          className="py-1.5 text-xs text-indigo-300"
                        >
                          Inspect
                        </Button>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          disabled={isBusy}
                          onClick={() => handleToggle(prov)}
                          className={`inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                            prov.enabled
                              ? "bg-rose-500/10 text-rose-300 hover:bg-rose-500/20 border border-rose-500/20"
                              : "bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20 border border-emerald-500/20"
                          }`}
                        >
                          <Power className="h-3.5 w-3.5" />
                          {prov.enabled ? "Disable" : "Enable"}
                        </button>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}

          {/* Configuration Modal */}
          <ProviderConfigModal
            isOpen={Boolean(configModal)}
            onClose={() => setConfigModal(null)}
            provider={configModal}
            allProviders={providers || []}
            onSave={saveConfiguration}
            busy={busy === configModal?.provider_id}
          />


          {/* Add Custom Provider Modal */}
          {addModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
              <div className="surface max-h-[90vh] w-full max-w-md overflow-y-auto p-6 rounded-2xl border border-white/10 shadow-2xl">
                <div className="flex items-center justify-between border-b border-white/10 pb-4">
                  <h3 className="text-lg font-bold text-white">Add New Custom Provider</h3>
                  <button onClick={() => setAddModal(false)} className="text-slate-400 hover:text-white">
                    <X className="h-5 w-5" />
                  </button>
                </div>

                <div className="mt-4 space-y-3 text-xs">
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Provider ID (slug)</label>
                    <input
                      type="text"
                      placeholder="e.g. custom_llm"
                      value={formState.provider_id}
                      onChange={(e) => setFormState({ ...formState, provider_id: e.target.value })}
                      className="w-full rounded-xl bg-black/40 px-3 py-2 text-xs text-white border border-white/10 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Display Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Custom LLM Gateway"
                      value={formState.provider_name}
                      onChange={(e) => setFormState({ ...formState, provider_name: e.target.value })}
                      className="w-full rounded-xl bg-black/40 px-3 py-2 text-xs text-white border border-white/10 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">API Key</label>
                    <input
                      type="password"
                      placeholder="sk-..."
                      value={formState.api_key}
                      onChange={(e) => setFormState({ ...formState, api_key: e.target.value })}
                      className="w-full rounded-xl bg-black/40 px-3 py-2 text-xs text-white border border-white/10 outline-none"
                    />
                  </div>
                </div>

                <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-white/10">
                  <Button variant="secondary" onClick={() => setAddModal(false)}>Cancel</Button>
                  <Button onClick={handleCreateProvider}>Create Provider</Button>
                </div>
              </div>
            </div>
          )}

          {/* Provider Detailed Inspection Drawer */}
          {drawerProvider && (
            <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm">
              <div className="h-full w-full max-w-md bg-[#101726] p-6 shadow-2xl overflow-y-auto border-l border-white/10">
                <div className="flex items-center justify-between border-b border-white/10 pb-4">
                  <div>
                    <span className="rounded bg-indigo-500/10 px-2 py-0.5 text-xs text-indigo-300">
                      Detailed Telemetry
                    </span>
                    <h3 className="text-xl font-bold text-white mt-1">
                      {drawerProvider.provider_name}
                    </h3>
                  </div>
                  <button
                    onClick={() => setDrawerProvider(null)}
                    className="text-slate-400 hover:text-white"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                <div className="mt-6 space-y-4 text-xs">
                  <div className="rounded-xl bg-white/[0.03] p-4">
                    <p className="text-slate-400 mb-1">Live Health Status</p>
                    <div className="flex items-center justify-between">
                      <Badge tone={drawerProvider.status === "healthy" ? "green" : "amber"}>
                        {drawerProvider.status}
                      </Badge>
                      <span className="text-slate-400 font-mono">
                        Latency: {drawerProvider.last_latency_ms}ms
                      </span>
                    </div>
                  </div>

                  <div className="rounded-xl bg-white/[0.03] p-4">
                    <p className="text-slate-400 mb-2 font-medium">Rate Limits & Priority</p>
                    <div className="grid grid-cols-2 gap-2 text-slate-300">
                      <div>RPM Limit: <span className="font-semibold text-white">{drawerProvider.rate_limit_rpm || 600}</span></div>
                      <div>TPM Limit: <span className="font-semibold text-white">{drawerProvider.rate_limit_tpm || 100000}</span></div>
                      <div>Timeout: <span className="font-semibold text-white">{drawerProvider.timeout_seconds || 30}s</span></div>
                      <div>Retries: <span className="font-semibold text-white">{drawerProvider.retry_count || 3}</span></div>
                    </div>
                  </div>

                  <div className="rounded-xl bg-black/40 p-4 font-mono text-[11px] text-emerald-400 border border-white/10 overflow-x-auto">
                    <p className="text-slate-400 font-sans mb-2 text-xs">Raw Configuration Object</p>
                    {JSON.stringify(drawerProvider, null, 2)}
                  </div>

                  <div className="pt-4 flex justify-between border-t border-white/10">
                    <Button
                      variant="secondary"
                      onClick={() => handleDeleteProvider(drawerProvider.provider_id)}
                      className="text-rose-400 hover:text-rose-300"
                    >
                      <Trash2 className="h-4 w-4" /> Delete Provider
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}

          <Toast message={toast} clear={() => setToast("")} />
        </>
      )}
    </AppShell>
  );
}

export default WithAdminAuth(ProvidersPage, "provider.manage");
