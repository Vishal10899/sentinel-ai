"use client";

import { useEffect, useState } from "react";
import {
  FlaskConical,
  Play,
  CheckCircle2,
  RotateCcw,
  Lightbulb,
  TrendingUp,
  AlertTriangle,
  ShieldCheck,
  RefreshCw,
  Layers,
  HelpCircle,
  Sliders,
  DollarSign
} from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import { api } from "../../lib/api";

export default function PolicySimulatorPage() {
  const [versions, setVersions] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);
  const [activeTab, setActiveTab] = useState("dry_run"); // "dry_run" | "what_if"

  // Simulation State
  const [maxCostInput, setMaxCostInput] = useState("0.05");
  const [blockedModelInput, setBlockedModelInput] = useState("");
  const [simResult, setSimResult] = useState(null);
  const [simulating, setSimulating] = useState(false);

  // What-If Scenario State
  const [whatIfTrafficMultiplier, setWhatIfTrafficMultiplier] = useState(1.5);
  const [whatIfPrimaryProvider, setWhatIfPrimaryProvider] = useState("openai");
  const [whatIfScenarioResult, setWhatIfScenarioResult] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [verData, recData] = await Promise.all([
        api.getPolicyVersions(),
        api.getOptimizationRecommendations(),
      ]);
      setVersions(verData || []);
      setRecommendations(recData || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunSimulation = async (e) => {
    e.preventDefault();
    try {
      setSimulating(true);
      const res = await api.runPolicySimulation({
        proposed_policy: {
          max_cost_per_request: parseFloat(maxCostInput) || 0.05,
          blocked_models: blockedModelInput ? [blockedModelInput] : [],
        },
      });
      setSimResult(res);
      setToast({ type: "success", message: "Policy simulation dry-run completed!" });
    } catch (err) {
      setToast({ type: "error", message: `Simulation failed: ${err.message}` });
    } finally {
      setSimulating(false);
    }
  };

  const handleRunWhatIfScenario = () => {
    const baseCost = 450.0;
    const estCost = baseCost * whatIfTrafficMultiplier * (whatIfPrimaryProvider === "ollama" ? 0.05 : 0.85);
    const latencyMs = whatIfPrimaryProvider === "ollama" ? 18 : 280;

    setWhatIfScenarioResult({
      projected_monthly_spend_usd: estCost,
      savings_vs_baseline_usd: (baseCost * whatIfTrafficMultiplier) - estCost,
      avg_latency_ms: latencyMs,
      traffic_growth_pct: (whatIfTrafficMultiplier - 1.0) * 100,
    });
  };

  const handlePublishVersion = async () => {
    try {
      const newVer = await api.publishPolicyVersion({
        policy_data: {
          max_cost_per_request: parseFloat(maxCostInput) || 0.05,
          blocked_models: blockedModelInput ? [blockedModelInput] : [],
        },
      });
      setToast({ type: "success", message: `Published Policy ${newVer.version_number}!` });
      loadData();
    } catch (err) {
      setToast({ type: "error", message: `Publish failed: ${err.message}` });
    }
  };

  const handleRollback = async (versionId) => {
    try {
      const rolled = await api.rollbackPolicyVersion(versionId);
      setToast({ type: "success", message: `Rolled back to ${rolled.version_number}!` });
      loadData();
    } catch (err) {
      setToast({ type: "error", message: `Rollback failed: ${err.message}` });
    }
  };

  const handleApplyRec = async (recId) => {
    try {
      await api.applyOptimizationRecommendation(recId);
      setToast({ type: "success", message: "Recommendation applied to active policy!" });
      loadData();
    } catch (err) {
      setToast({ type: "error", message: `Apply failed: ${err.message}` });
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageTitle
          title="Enterprise Policy Simulator & What-If Studio"
          subtitle="Dry-run policy impact analysis, what-if scenario forecasting, zero-downtime policy versioning & rollback, and AI optimization advisor."
          action={
            <Button variant="zinc" onClick={loadData}>
              <RefreshCw className="h-4 w-4" /> Refresh Advisor
            </Button>
          }
        />

        {toast && <Toast type={toast.type} message={toast.message} onClose={() => setToast(null)} />}

        {/* Tab Selector */}
        <div className="flex gap-2 border-b border-white/10 pb-3">
          <button
            onClick={() => setActiveTab("dry_run")}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-colors flex items-center gap-2 ${
              activeTab === "dry_run"
                ? "bg-indigo-600 text-white"
                : "bg-black/30 text-slate-400 hover:text-white"
            }`}
          >
            <FlaskConical className="h-4 w-4" /> Dry-Run Policy Simulator
          </button>

          <button
            onClick={() => setActiveTab("what_if")}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-colors flex items-center gap-2 ${
              activeTab === "what_if"
                ? "bg-indigo-600 text-white"
                : "bg-black/30 text-slate-400 hover:text-white"
            }`}
          >
            <HelpCircle className="h-4 w-4" /> What-If Scenario Analysis
          </button>
        </div>

        {loading ? (
          <LoadingCard title="Loading Policy Simulator & AI Optimization Advisor..." />
        ) : error ? (
          <ErrorCard title="Simulator Load Error" message={error} onRetry={loadData} />
        ) : (
          <>
            {activeTab === "dry_run" ? (
              /* Dry-Run Policy Simulator Card */
              <div className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <FlaskConical className="h-4 w-4 text-indigo-400" /> Dry-Run Policy Impact Analysis Simulator
                </h3>

                <form onSubmit={handleRunSimulation} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-slate-300 block mb-1">Max Cost Per Request ($)</label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      value={maxCostInput}
                      onChange={(e) => setMaxCostInput(e.target.value)}
                      className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 font-mono"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-300 block mb-1">Block Model (Optional)</label>
                    <input
                      type="text"
                      value={blockedModelInput}
                      onChange={(e) => setBlockedModelInput(e.target.value)}
                      placeholder="e.g. gpt-4o"
                      className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 font-mono"
                    />
                  </div>

                  <div className="flex items-end gap-2">
                    <Button type="submit" disabled={simulating} className="flex-1">
                      <Play className="h-4 w-4" /> {simulating ? "Simulating..." : "Run Dry-Run Simulation"}
                    </Button>
                    <Button type="button" variant="zinc" onClick={handlePublishVersion}>
                      Publish Version
                    </Button>
                  </div>
                </form>

                {/* Simulation Result Output */}
                {simResult && (
                  <div className="mt-4 rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-5 space-y-3">
                    <h4 className="text-sm font-bold text-white flex items-center justify-between">
                      <span>Simulation Impact Analysis Output</span>
                      <Badge variant={simResult.impact_percentage > 20 ? "amber" : "emerald"}>
                        {simResult.impact_percentage}% Workload Impacted
                      </Badge>
                    </h4>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
                      <div className="p-3 rounded-lg bg-black/40 border border-white/5">
                        <span className="text-slate-400 text-[10px] block">Total Sample:</span>
                        <span className="text-white font-bold">{simResult.total_requests} requests</span>
                      </div>
                      <div className="p-3 rounded-lg bg-black/40 border border-white/5">
                        <span className="text-slate-400 text-[10px] block">Allowed / Blocked:</span>
                        <span className="text-emerald-400 font-bold">{simResult.allowed_count}</span> / <span className="text-rose-400 font-bold">{simResult.blocked_count}</span>
                      </div>
                      <div className="p-3 rounded-lg bg-black/40 border border-white/5">
                        <span className="text-slate-400 text-[10px] block">Cost Delta:</span>
                        <span className="text-emerald-400 font-bold">${simResult.cost_delta_usd.toFixed(4)}</span>
                      </div>
                      <div className="p-3 rounded-lg bg-black/40 border border-white/5">
                        <span className="text-slate-400 text-[10px] block">Latency Delta:</span>
                        <span className="text-cyan-300 font-bold">{simResult.latency_delta_ms} ms</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              /* What-If Scenario Analysis Studio */
              <div className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <HelpCircle className="h-4 w-4 text-cyan-400" /> What-If Scenario Analysis & Capacity Forecasting
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-slate-300 block mb-1">Traffic Growth Multiplier</label>
                    <select
                      value={whatIfTrafficMultiplier}
                      onChange={(e) => setWhatIfTrafficMultiplier(parseFloat(e.target.value))}
                      className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                    >
                      <option value={1.25}>+25% Traffic Growth</option>
                      <option value={1.5}>+50% Traffic Growth</option>
                      <option value={2.0}>+100% Traffic Spikes (2x Load)</option>
                      <option value={5.0}>+400% Extreme Scaling (5x Load)</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-300 block mb-1">Primary Route Strategy Target</label>
                    <select
                      value={whatIfPrimaryProvider}
                      onChange={(e) => setWhatIfPrimaryProvider(e.target.value)}
                      className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                    >
                      <option value="openai">OpenAI Cloud Tier</option>
                      <option value="gemini">Google Gemini Tier</option>
                      <option value="ollama">Self-Hosted Ollama (Local Free)</option>
                    </select>
                  </div>

                  <div className="flex items-end">
                    <Button onClick={handleRunWhatIfScenario} className="w-full">
                      <TrendingUp className="h-4 w-4" /> Calculate What-If Forecast
                    </Button>
                  </div>
                </div>

                {whatIfScenarioResult && (
                  <div className="mt-4 rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-5 space-y-3">
                    <h4 className="text-sm font-bold text-white flex items-center justify-between">
                      <span>Hypothetical Forecast Output</span>
                      <Badge variant="cyan">+{whatIfScenarioResult.traffic_growth_pct.toFixed(0)}% Growth Projection</Badge>
                    </h4>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
                      <div className="p-3 rounded-lg bg-black/40 border border-white/5">
                        <span className="text-slate-400 text-[10px] block">Est. Monthly Spend:</span>
                        <span className="text-white font-bold">${whatIfScenarioResult.projected_monthly_spend_usd.toFixed(2)}</span>
                      </div>
                      <div className="p-3 rounded-lg bg-black/40 border border-white/5">
                        <span className="text-slate-400 text-[10px] block">Projected Savings:</span>
                        <span className="text-emerald-400 font-bold">${whatIfScenarioResult.savings_vs_baseline_usd.toFixed(2)}</span>
                      </div>
                      <div className="p-3 rounded-lg bg-black/40 border border-white/5">
                        <span className="text-slate-400 text-[10px] block">Projected Avg Latency:</span>
                        <span className="text-cyan-300 font-bold">{whatIfScenarioResult.avg_latency_ms} ms</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* AI Optimization Advisor Recommendations Grid */}
            <div className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-amber-400" /> AI Optimization Advisor Recommendations
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {recommendations.map((rec) => (
                  <div key={rec.id} className="rounded-xl border border-white/10 bg-black/40 p-4 space-y-3 flex flex-col justify-between">
                    <div className="space-y-2">
                      <div className="flex justify-between items-start gap-2">
                        <Badge variant={rec.priority === "HIGH" ? "amber" : "cyan"}>{rec.type}</Badge>
                        <span className="text-[10px] font-mono text-emerald-400 font-bold">Est. Savings: {rec.estimated_savings}</span>
                      </div>
                      <p className="text-xs text-slate-200">{rec.recommendation}</p>
                      <p className="text-[10px] text-slate-400">{rec.impact}</p>
                    </div>

                    <Button size="xs" variant="zinc" onClick={() => handleApplyRec(rec.id)}>
                      Apply Recommendation
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            {/* Policy Versions Timeline & Rollback */}
            <div className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Layers className="h-4 w-4 text-indigo-400" /> Immutable Policy Versioning & Zero-Downtime Rollback
              </h3>

              <div className="space-y-3">
                {versions.map((ver) => (
                  <div
                    key={ver.id}
                    className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                      ver.is_active
                        ? "border-emerald-500/40 bg-emerald-500/10"
                        : "border-white/5 bg-black/40"
                    }`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-white">Version {ver.version_number}</span>
                        {ver.is_active && <Badge variant="emerald">ACTIVE</Badge>}
                        <span className="text-[10px] text-slate-400 font-mono">{new Date(ver.created_at).toLocaleString()}</span>
                      </div>
                      <p className="text-xs text-slate-300 font-mono">
                        Max Cost: ${ver.policy_data?.max_cost_per_request || 0.05} | Blocked: {ver.policy_data?.blocked_models?.join(", ") || "None"}
                      </p>
                    </div>

                    {!ver.is_active && (
                      <Button size="xs" variant="zinc" onClick={() => handleRollback(ver.id)}>
                        <RotateCcw className="h-3.5 w-3.5" /> Rollback to V{ver.version_number}
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
