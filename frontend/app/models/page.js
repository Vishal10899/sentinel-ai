"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Search,
  Cpu,
  Zap,
  Award,
  Sparkles,
  ShieldCheck,
  Eye,
  Mic,
  Code2,
  Layers,
  Filter,
  DollarSign,
  Clock,
  CheckCircle2,
  AlertTriangle,
  X,
  ChevronRight,
  BarChart3,
  SlidersHorizontal,
} from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, ErrorCard, LoadingCard, EmptyState } from "../../components/ui";
import { api } from "../../lib/api";

const PROVIDER_THEMES = {
  openai: {
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    text: "text-emerald-300",
    badge: "green",
    label: "OpenAI",
  },
  gemini: {
    bg: "bg-sky-500/10",
    border: "border-sky-500/20",
    text: "text-sky-300",
    badge: "indigo",
    label: "Google Gemini",
  },
  anthropic: {
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
    text: "text-amber-300",
    badge: "amber",
    label: "Anthropic",
  },
  ollama: {
    bg: "bg-purple-500/10",
    border: "border-purple-500/20",
    text: "text-purple-300",
    badge: "slate",
    label: "Ollama (Local)",
  },
};

export default function ModelsPage() {
  const [models, setModels] = useState(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [provider, setProvider] = useState("all");
  const [capability, setCapability] = useState("all");
  const [sortBy, setSortBy] = useState("priority");
  const [selectedModel, setSelectedModel] = useState(null);

  const loadCatalog = () => {
    setError("");
    api
      .models()
      .then(setModels)
      .catch((e) => setError(e.message));
  };

  useEffect(loadCatalog, []);

  // Compute available filter options dynamically
  const categories = useMemo(() => {
    if (!models) return [];
    return ["all", ...new Set(models.map((m) => m.category || "chat"))];
  }, [models]);

  const providers = useMemo(() => {
    if (!models) return [];
    return ["all", ...new Set(models.map((m) => m.provider_id))];
  }, [models]);

  const capabilitiesList = useMemo(() => {
    if (!models) return [];
    return ["all", ...new Set(models.flatMap((m) => m.capabilities || []))];
  }, [models]);

  // KPI Statistics
  const stats = useMemo(() => {
    if (!models || models.length === 0)
      return { count: 0, providers: 0, maxContext: "0", avgLatency: 0 };
    const provCount = new Set(models.map((m) => m.provider_id)).size;
    const maxCtx = Math.max(...models.map((m) => m.context_window || 0));
    const avgLat = Math.round(
      models.reduce((acc, m) => acc + (m.average_latency_ms || 0), 0) /
        models.length
    );
    return {
      count: models.length,
      providers: provCount,
      maxContext:
        maxCtx >= 1000000
          ? `${(maxCtx / 1000000).toFixed(1)}M`
          : `${(maxCtx / 1000).toFixed(0)}K`,
      avgLatency: avgLat,
    };
  }, [models]);

  // Filter & Sort list
  const filteredList = useMemo(() => {
    if (!models) return [];
    let list = models.filter((m) => {
      const matchSearch = `${m.display_name} ${m.model_id} ${m.provider_name}`
        .toLowerCase()
        .includes(search.toLowerCase());
      const matchCategory =
        category === "all" ||
        (m.category || "chat").toLowerCase() === category.toLowerCase();
      const matchProvider =
        provider === "all" || m.provider_id === provider;
      const matchCapability =
        capability === "all" || (m.capabilities || []).includes(capability);
      return matchSearch && matchCategory && matchProvider && matchCapability;
    });

    return list.sort((a, b) => {
      if (sortBy === "latency") return a.average_latency_ms - b.average_latency_ms;
      if (sortBy === "quality") return (b.quality_score || 0) - (a.quality_score || 0);
      if (sortBy === "reasoning") return (b.reasoning_score || 0) - (a.reasoning_score || 0);
      if (sortBy === "cost")
        return (
          Number(a.cost_per_1k_input_tokens) - Number(b.cost_per_1k_input_tokens)
        );
      if (sortBy === "context") return b.context_window - a.context_window;
      return a.priority - b.priority;
    });
  }, [models, search, category, provider, capability, sortBy]);

  return (
    <AppShell
      title="Enterprise Model Registry"
      subtitle="Single source of truth for all deployed & supported AI models"
    >
      <PageTitle
        eyebrow="Model Catalog & Metadata"
        title="Enterprise AI Models"
        copy="Inspect latency SLA, context windows, benchmark scores, token pricing, and capability flags across all registered providers."
      />

      {error ? (
        <ErrorCard error={error} retry={loadCatalog} />
      ) : !models ? (
        <LoadingCard label="Fetching Enterprise Model Registry..." />
      ) : (
        <>
          {/* Top KPI Statistics */}
          <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
            <div className="surface p-4 flex items-center gap-3">
              <div className="rounded-xl bg-indigo-500/10 p-3 text-indigo-400">
                <Cpu className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.count}</p>
                <p className="text-xs text-slate-400">Registered Models</p>
              </div>
            </div>

            <div className="surface p-4 flex items-center gap-3">
              <div className="rounded-xl bg-sky-500/10 p-3 text-sky-400">
                <Layers className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.providers}</p>
                <p className="text-xs text-slate-400">Active Providers</p>
              </div>
            </div>

            <div className="surface p-4 flex items-center gap-3">
              <div className="rounded-xl bg-emerald-500/10 p-3 text-emerald-400">
                <Zap className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.maxContext}</p>
                <p className="text-xs text-slate-400">Max Context Window</p>
              </div>
            </div>

            <div className="surface p-4 flex items-center gap-3">
              <div className="rounded-xl bg-amber-500/10 p-3 text-amber-400">
                <Clock className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.avgLatency}ms</p>
                <p className="text-xs text-slate-400">Avg Latency SLA</p>
              </div>
            </div>
          </div>

          {/* Search & Filter Controls */}
          <div className="surface mb-6 p-4 flex flex-col gap-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
              {/* Search input */}
              <div className="relative flex-1">
                <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by model name, ID, or provider..."
                  className="w-full rounded-xl bg-black/30 py-2.5 pl-9 pr-4 text-sm text-white outline-none border border-white/10 focus:border-indigo-500/50"
                />
                {search && (
                  <button
                    onClick={() => setSearch("")}
                    className="absolute right-3 top-3 text-slate-500 hover:text-white"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>

              {/* Filters & Sort dropdowns */}
              <div className="flex flex-wrap gap-2">
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="rounded-xl border border-white/10 bg-[#121827] px-3 py-2 text-xs text-slate-300 outline-none"
                >
                  <option value="all">All Providers</option>
                  {providers.filter((p) => p !== "all").map((p) => (
                    <option key={p} value={p}>
                      {PROVIDER_THEMES[p]?.label || p}
                    </option>
                  ))}
                </select>

                <select
                  value={capability}
                  onChange={(e) => setCapability(e.target.value)}
                  className="rounded-xl border border-white/10 bg-[#121827] px-3 py-2 text-xs text-slate-300 outline-none"
                >
                  <option value="all">All Capabilities</option>
                  {capabilitiesList
                    .filter((c) => c !== "all")
                    .map((c) => (
                      <option key={c} value={c}>
                        {c.replace("_", " ")}
                      </option>
                    ))}
                </select>

                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="rounded-xl border border-white/10 bg-[#121827] px-3 py-2 text-xs text-indigo-300 outline-none"
                >
                  <option value="priority">Sort: Priority Rank</option>
                  <option value="latency">Sort: Latency (Fastest)</option>
                  <option value="quality">Sort: Quality Score</option>
                  <option value="reasoning">Sort: Reasoning Score</option>
                  <option value="cost">Sort: Cost (Lowest)</option>
                  <option value="context">Sort: Context Window</option>
                </select>
              </div>
            </div>

            {/* Category Pills */}
            <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-white/[0.06]">
              <span className="text-xs text-slate-400 mr-2 flex items-center gap-1">
                <Filter className="h-3 w-3" /> Category:
              </span>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategory(cat)}
                  className={`rounded-lg px-3 py-1 text-xs capitalize transition ${
                    category === cat
                      ? "bg-indigo-500 text-white font-medium"
                      : "bg-white/[0.04] text-slate-400 hover:bg-white/[0.08] hover:text-slate-200"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Model Cards Grid */}
          {filteredList.length === 0 ? (
            <EmptyState
              title="No models match search parameters"
              copy="Try resetting filters or searching for another keyword."
            />
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {filteredList.map((m) => {
                const theme = PROVIDER_THEMES[m.provider_id] || {
                  bg: "bg-slate-500/10",
                  border: "border-slate-500/20",
                  text: "text-slate-300",
                  label: m.provider_name,
                };

                return (
                  <article
                    key={`${m.provider_id}-${m.model_id}`}
                    onClick={() => setSelectedModel(m)}
                    className="surface hover:border-indigo-500/40 cursor-pointer p-5 transition flex flex-col justify-between"
                  >
                    <div>
                      {/* Provider & Category Header */}
                      <div className="flex items-center justify-between gap-2">
                        <span
                          className={`rounded-md px-2 py-0.5 text-[11px] font-semibold border ${theme.bg} ${theme.border} ${theme.text}`}
                        >
                          {theme.label}
                        </span>
                        <div className="flex items-center gap-1">
                          <span className="rounded-md bg-white/[0.06] px-2 py-0.5 text-[10px] text-slate-400 capitalize">
                            {m.category || "chat"}
                          </span>
                          {m.deprecated ? (
                            <Badge tone="amber">Deprecated</Badge>
                          ) : m.enabled ? (
                            <Badge tone="green">Enabled</Badge>
                          ) : (
                            <Badge tone="slate">Disabled</Badge>
                          )}
                        </div>
                      </div>

                      {/* Display Name & Model ID */}
                      <div className="mt-3">
                        <h3 className="text-base font-semibold text-white">
                          {m.display_name}
                        </h3>
                        <p className="font-mono text-xs text-slate-400 mt-0.5">
                          {m.model_id}
                        </p>
                      </div>

                      {/* Benchmark Scores Visualization */}
                      {(m.quality_score > 0 ||
                        m.reasoning_score > 0 ||
                        m.speed_score > 0) && (
                        <div className="mt-4 grid grid-cols-3 gap-2 rounded-xl bg-black/20 p-2.5 text-center">
                          <div>
                            <p className="text-[10px] uppercase tracking-wider text-slate-400">
                              Reasoning
                            </p>
                            <p className="text-xs font-bold text-amber-300">
                              {m.reasoning_score || "--"}
                            </p>
                          </div>
                          <div>
                            <p className="text-[10px] uppercase tracking-wider text-slate-400">
                              Speed
                            </p>
                            <p className="text-xs font-bold text-emerald-300">
                              {m.speed_score || "--"}
                            </p>
                          </div>
                          <div>
                            <p className="text-[10px] uppercase tracking-wider text-slate-400">
                              Quality
                            </p>
                            <p className="text-xs font-bold text-sky-300">
                              {m.quality_score || "--"}
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Specs Grid */}
                      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                        <div className="rounded-lg bg-white/[0.03] p-2.5">
                          <p className="text-slate-500 text-[11px]">Input Cost / 1K</p>
                          <p className="mt-0.5 font-semibold text-emerald-400">
                            ${m.cost_per_1k_input_tokens}
                          </p>
                        </div>
                        <div className="rounded-lg bg-white/[0.03] p-2.5">
                          <p className="text-slate-500 text-[11px]">Output Cost / 1K</p>
                          <p className="mt-0.5 font-semibold text-emerald-400">
                            ${m.cost_per_1k_output_tokens}
                          </p>
                        </div>
                        <div className="rounded-lg bg-white/[0.03] p-2.5">
                          <p className="text-slate-500 text-[11px]">Context Window</p>
                          <p className="mt-0.5 font-semibold text-slate-200">
                            {m.context_window >= 1000000
                              ? `${(m.context_window / 1000000).toFixed(1)}M`
                              : `${(m.context_window / 1000).toFixed(0)}K`}{" "}
                            tokens
                          </p>
                        </div>
                        <div className="rounded-lg bg-white/[0.03] p-2.5">
                          <p className="text-slate-500 text-[11px]">Average Latency</p>
                          <p className="mt-0.5 font-semibold text-slate-200">
                            {m.average_latency_ms} ms
                          </p>
                        </div>
                      </div>

                      {/* Modality & Capability Badges */}
                      <div className="mt-3 flex flex-wrap gap-1">
                        {m.supports_vision && (
                          <span className="inline-flex items-center gap-1 rounded bg-sky-400/10 px-2 py-0.5 text-[10px] font-medium text-sky-300">
                            <Eye className="h-3 w-3" /> Vision
                          </span>
                        )}
                        {m.supports_audio && (
                          <span className="inline-flex items-center gap-1 rounded bg-purple-400/10 px-2 py-0.5 text-[10px] font-medium text-purple-300">
                            <Mic className="h-3 w-3" /> Audio
                          </span>
                        )}
                        {m.supports_function_calling && (
                          <span className="inline-flex items-center gap-1 rounded bg-indigo-400/10 px-2 py-0.5 text-[10px] font-medium text-indigo-300">
                            <Code2 className="h-3 w-3" /> Tools
                          </span>
                        )}
                        {m.supports_streaming && (
                          <span className="inline-flex items-center gap-1 rounded bg-emerald-400/10 px-2 py-0.5 text-[10px] font-medium text-emerald-300">
                            <Zap className="h-3 w-3" /> Stream
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="mt-4 flex items-center justify-between pt-3 border-t border-white/[0.06] text-xs text-indigo-400 font-medium">
                      <span>Inspect Specifications</span>
                      <ChevronRight className="h-4 w-4" />
                    </div>
                  </article>
                );
              })}
            </div>
          )}

          {/* Model Specification Detail Modal */}
          {selectedModel && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
              <div className="surface max-h-[90vh] w-full max-w-2xl overflow-y-auto p-6 rounded-2xl border border-white/10 shadow-2xl">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="rounded-md bg-indigo-500/10 px-2.5 py-1 text-xs font-semibold text-indigo-300">
                      {selectedModel.provider_name}
                    </span>
                    <h2 className="mt-2 text-xl font-bold text-white">
                      {selectedModel.display_name}
                    </h2>
                    <p className="font-mono text-xs text-slate-400">
                      {selectedModel.model_id}
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedModel(null)}
                    className="rounded-lg bg-white/5 p-2 text-slate-400 hover:bg-white/10 hover:text-white"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                <div className="mt-6 grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
                  <div className="rounded-xl bg-white/[0.04] p-3">
                    <p className="text-slate-400">Category</p>
                    <p className="mt-1 text-sm font-semibold capitalize text-white">
                      {selectedModel.category || "chat"}
                    </p>
                  </div>
                  <div className="rounded-xl bg-white/[0.04] p-3">
                    <p className="text-slate-400">Context Window</p>
                    <p className="mt-1 text-sm font-semibold text-white">
                      {selectedModel.context_window.toLocaleString()} tokens
                    </p>
                  </div>
                  <div className="rounded-xl bg-white/[0.04] p-3">
                    <p className="text-slate-400">Max Output</p>
                    <p className="mt-1 text-sm font-semibold text-white">
                      {selectedModel.max_output_tokens
                        ? selectedModel.max_output_tokens.toLocaleString()
                        : "N/A"}{" "}
                      tokens
                    </p>
                  </div>
                  <div className="rounded-xl bg-white/[0.04] p-3">
                    <p className="text-slate-400">Latency SLA</p>
                    <p className="mt-1 text-sm font-semibold text-white">
                      {selectedModel.average_latency_ms} ms
                    </p>
                  </div>
                </div>

                <div className="mt-6">
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Pricing Breakdown (USD)
                  </h4>
                  <div className="mt-2 grid grid-cols-2 gap-3 text-xs">
                    <div className="rounded-xl bg-emerald-500/5 border border-emerald-500/20 p-3">
                      <p className="text-slate-400">Input Token Rate</p>
                      <p className="mt-1 text-base font-bold text-emerald-300">
                        ${selectedModel.cost_per_1k_input_tokens} / 1K tokens
                      </p>
                      <p className="text-[11px] text-slate-500 mt-1">
                        ($
                        {(
                          Number(selectedModel.cost_per_1k_input_tokens) * 1000
                        ).toFixed(4)}{" "}
                        / 1M tokens)
                      </p>
                    </div>

                    <div className="rounded-xl bg-emerald-500/5 border border-emerald-500/20 p-3">
                      <p className="text-slate-400">Output Token Rate</p>
                      <p className="mt-1 text-base font-bold text-emerald-300">
                        ${selectedModel.cost_per_1k_output_tokens} / 1K tokens
                      </p>
                      <p className="text-[11px] text-slate-500 mt-1">
                        ($
                        {(
                          Number(selectedModel.cost_per_1k_output_tokens) * 1000
                        ).toFixed(4)}{" "}
                        / 1M tokens)
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mt-6">
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Supported Capabilities
                  </h4>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {selectedModel.capabilities.map((cap) => (
                      <span
                        key={cap}
                        className="rounded-lg bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 text-xs text-indigo-300"
                      >
                        {cap.replace("_", " ")}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mt-6">
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Raw API Metadata Object
                  </h4>
                  <pre className="mt-2 max-h-40 overflow-auto rounded-xl bg-black/40 p-3 text-[11px] font-mono text-emerald-400 border border-white/10">
                    {JSON.stringify(selectedModel, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </AppShell>
  );
}
