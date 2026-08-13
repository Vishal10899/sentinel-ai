"use client";

import { useEffect, useState } from "react";
import { Cpu, Zap, Search, Play, CheckCircle2, Sliders, ShieldCheck, HelpCircle, Layers, ArrowRight, RefreshCw, BarChart2 } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import { api } from "../../lib/api";

export default function RoutingCenterPage() {
  const [capabilities, setCapabilities] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  // Simulator State
  const [promptText, setPromptText] = useState("Write a Python function to implement a binary search tree with insert and delete operations.");
  const [strategyOverride, setStrategyOverride] = useState("ADAPTIVE_SMART");
  const [routingResult, setRoutingResult] = useState(null);
  const [simulating, setSimulating] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [capData, stratData] = await Promise.all([
        api.getModelCapabilities(),
        api.getRoutingStrategies(),
      ]);
      setCapabilities(capData || []);
      setStrategies(stratData || []);
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

  const handleSimulateRouting = async (e) => {
    e.preventDefault();
    try {
      setSimulating(true);
      const res = await api.performAdaptiveRouting({
        prompt: promptText,
        strategy_override: strategyOverride,
      });
      setRoutingResult(res);
    } catch (err) {
      setToast({ type: "error", message: `Simulation failed: ${err.message}` });
    } finally {
      setSimulating(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageTitle
          title="Adaptive AI Routing & Orchestration Center"
          subtitle="Intent classification, workload profiling, model capability matching, and decision explainability."
          action={
            <Button variant="zinc" onClick={loadData}>
              <RefreshCw className="h-4 w-4" /> Refresh Capabilities
            </Button>
          }
        />

        {toast && <Toast type={toast.type} message={toast.message} onClose={() => setToast(null)} />}

        {loading ? (
          <LoadingCard title="Loading Model Capability Catalog & Routing Strategies..." />
        ) : error ? (
          <ErrorCard title="Routing Center Load Error" message={error} onRetry={loadData} />
        ) : (
          <>
            {/* Live Intent & Routing Simulator */}
            <div className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Cpu className="h-4 w-4 text-indigo-400" /> Interactive Intent Detector & Live Routing Simulator
              </h3>

              <form onSubmit={handleSimulateRouting} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-2">
                    <label className="text-xs font-semibold text-slate-300 block mb-1">Simulated User Prompt</label>
                    <textarea
                      rows={3}
                      required
                      value={promptText}
                      onChange={(e) => setPromptText(e.target.value)}
                      className="w-full rounded-xl border border-white/10 bg-black/40 p-3 text-xs text-white outline-none focus:border-indigo-500 font-mono"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-300 block mb-1">Routing Strategy</label>
                    <select
                      value={strategyOverride}
                      onChange={(e) => setStrategyOverride(e.target.value)}
                      className="w-full rounded-xl border border-white/10 bg-black/40 p-3 text-xs text-white outline-none focus:border-indigo-500"
                    >
                      {strategies.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name}
                        </option>
                      ))}
                    </select>

                    <Button type="submit" className="w-full mt-4" disabled={simulating}>
                      {simulating ? "Simulating..." : "Simulate Adaptive Routing"}
                    </Button>
                  </div>
                </div>
              </form>

              {/* Simulation Result */}
              {routingResult && (
                <div className="mt-4 rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-5 space-y-3">
                  <div className="flex flex-wrap justify-between items-center gap-2">
                    <div>
                      <span className="text-[11px] text-indigo-300 font-bold uppercase tracking-wider">Detected Intent:</span>
                      <h4 className="text-lg font-extrabold text-white flex items-center gap-2">
                        {routingResult.intent_detected} <Badge variant="emerald">{(routingResult.confidence * 100).toFixed(0)}% Confidence</Badge>
                      </h4>
                    </div>

                    <div className="text-right">
                      <span className="text-[11px] text-slate-400 block">Selected Provider & Model:</span>
                      <span className="text-sm font-extrabold text-cyan-300 font-mono">
                        {routingResult.selected_provider} / {routingResult.selected_model}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 font-mono bg-black/40 p-3 rounded-lg border border-white/5">
                    {routingResult.explanation_text}
                  </p>

                  {/* Candidate Scores Table */}
                  {routingResult.candidate_scores?.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[11px] font-bold text-slate-300">Candidate Models Evaluated:</span>
                      <div className="space-y-1 text-xs font-mono">
                        {routingResult.candidate_scores.map((cand, idx) => (
                          <div key={idx} className="flex justify-between items-center p-2 rounded bg-black/30 border border-white/5">
                            <span className="text-slate-200">
                              {cand.provider_id} / {cand.model_id}
                            </span>
                            <span className="text-emerald-400 font-bold">Score: {cand.score}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Model Capability Catalog */}
            <div className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <BarChart2 className="h-4 w-4 text-cyan-400" /> Catalog Model Capabilities & Performance Scores
              </h3>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="border-b border-white/10 bg-white/[0.02] uppercase text-[10px] text-slate-400 font-bold">
                    <tr>
                      <th className="p-3">Provider / Model</th>
                      <th className="p-3">Context Window</th>
                      <th className="p-3">Vision</th>
                      <th className="p-3">Tools</th>
                      <th className="p-3">Quality Score</th>
                      <th className="p-3">Cost Score</th>
                      <th className="p-3">Latency Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/10 font-mono text-[11px]">
                    {capabilities.map((cap) => (
                      <tr key={`${cap.provider_id}-${cap.model_id}`} className="hover:bg-white/[0.02]">
                        <td className="p-3 font-bold text-white">
                          {cap.provider_id} / {cap.model_id}
                        </td>
                        <td className="p-3 text-cyan-300">{cap.context_window.toLocaleString()} tokens</td>
                        <td className="p-3">
                          <Badge variant={cap.supports_vision ? "emerald" : "zinc"}>{cap.supports_vision ? "YES" : "NO"}</Badge>
                        </td>
                        <td className="p-3">
                          <Badge variant={cap.supports_tools ? "emerald" : "zinc"}>{cap.supports_tools ? "YES" : "NO"}</Badge>
                        </td>
                        <td className="p-3 text-emerald-400 font-bold">{(cap.quality_score * 100).toFixed(0)}%</td>
                        <td className="p-3 text-indigo-300 font-bold">{(cap.cost_score * 100).toFixed(0)}%</td>
                        <td className="p-3 text-amber-300 font-bold">{(cap.latency_score * 100).toFixed(0)}%</td>
                      </tr>
                    ))}
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
