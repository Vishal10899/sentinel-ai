"use client";

import { useEffect, useState } from "react";
import { HelpCircle, Play, ShieldAlert, ArrowRightLeft, DollarSign, Clock, RefreshCw, Layers } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import { api } from "../../lib/api";

export default function WhatIfCenterPage() {
  const [scenarioType, setScenarioType] = useState("DISABLE_MODEL");
  const [modelInput, setModelInput] = useState("gpt-4o");
  const [budgetCutInput, setBudgetCutInput] = useState("30");
  const [providerInput, setProviderInput] = useState("openai");
  const [latencyInput, setLatencyInput] = useState("3000");

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const handleRunScenario = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      let params = {};
      if (scenarioType === "DISABLE_MODEL") params = { model_id: modelInput };
      else if (scenarioType === "BUDGET_CUT") params = { reduction_percentage: parseFloat(budgetCutInput) };
      else if (scenarioType === "PROVIDER_OUTAGE") params = { provider_id: providerInput };
      else if (scenarioType === "LATENCY_THRESHOLD") params = { max_latency_ms: parseInt(latencyInput) };

      const res = await api.runWhatIfScenario({
        scenario_type: scenarioType,
        parameters: params,
      });
      setResult(res);
      setToast({ type: "success", message: `What-If Scenario '${scenarioType}' analyzed!` });
    } catch (err) {
      setToast({ type: "error", message: `Scenario failed: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageTitle
          title="Enterprise What-If Scenario Analysis Center"
          subtitle="Simulate hypothetical production scenarios ('What if GPT-4 is disabled?', 'What if budget drops 30%?', 'What if OpenAI has an outage?')."
        />

        {toast && <Toast type={toast.type} message={toast.message} onClose={() => setToast(null)} />}

        {/* Scenario Configurator Card */}
        <div className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <HelpCircle className="h-4 w-4 text-indigo-400" /> Select Hypothetical Enterprise Scenario
          </h3>

          <form onSubmit={handleRunScenario} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              <button
                type="button"
                onClick={() => setScenarioType("DISABLE_MODEL")}
                className={`p-4 rounded-xl border text-left transition ${
                  scenarioType === "DISABLE_MODEL" ? "border-indigo-500 bg-indigo-500/10 text-white font-bold" : "border-white/10 bg-black/30 text-slate-400 hover:text-white"
                }`}
              >
                <span className="block text-xs">Scenario A</span>
                <span className="text-sm">Disable Model (GPT-4)</span>
              </button>

              <button
                type="button"
                onClick={() => setScenarioType("BUDGET_CUT")}
                className={`p-4 rounded-xl border text-left transition ${
                  scenarioType === "BUDGET_CUT" ? "border-indigo-500 bg-indigo-500/10 text-white font-bold" : "border-white/10 bg-black/30 text-slate-400 hover:text-white"
                }`}
              >
                <span className="block text-xs">Scenario B</span>
                <span className="text-sm">Budget Cut (30%)</span>
              </button>

              <button
                type="button"
                onClick={() => setScenarioType("PROVIDER_OUTAGE")}
                className={`p-4 rounded-xl border text-left transition ${
                  scenarioType === "PROVIDER_OUTAGE" ? "border-indigo-500 bg-indigo-500/10 text-white font-bold" : "border-white/10 bg-black/30 text-slate-400 hover:text-white"
                }`}
              >
                <span className="block text-xs">Scenario C</span>
                <span className="text-sm">Provider Outage</span>
              </button>

              <button
                type="button"
                onClick={() => setScenarioType("LATENCY_THRESHOLD")}
                className={`p-4 rounded-xl border text-left transition ${
                  scenarioType === "LATENCY_THRESHOLD" ? "border-indigo-500 bg-indigo-500/10 text-white font-bold" : "border-white/10 bg-black/30 text-slate-400 hover:text-white"
                }`}
              >
                <span className="block text-xs">Scenario D</span>
                <span className="text-sm">Latency Threshold</span>
              </button>
            </div>

            {/* Dynamic Parameters Form */}
            <div className="rounded-xl border border-white/10 bg-black/40 p-4 space-y-3">
              {scenarioType === "DISABLE_MODEL" && (
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Target Model ID</label>
                  <input
                    type="text"
                    required
                    value={modelInput}
                    onChange={(e) => setModelInput(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-black/50 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 font-mono"
                  />
                </div>
              )}

              {scenarioType === "BUDGET_CUT" && (
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Budget Reduction (%)</label>
                  <input
                    type="number"
                    required
                    value={budgetCutInput}
                    onChange={(e) => setBudgetCutInput(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-black/50 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 font-mono"
                  />
                </div>
              )}

              {scenarioType === "PROVIDER_OUTAGE" && (
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Provider ID</label>
                  <input
                    type="text"
                    required
                    value={providerInput}
                    onChange={(e) => setProviderInput(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-black/50 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 font-mono"
                  />
                </div>
              )}

              {scenarioType === "LATENCY_THRESHOLD" && (
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Max Latency Cutoff (ms)</label>
                  <input
                    type="number"
                    required
                    value={latencyInput}
                    onChange={(e) => setLatencyInput(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-black/50 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 font-mono"
                  />
                </div>
              )}

              <Button type="submit" disabled={loading} className="w-full">
                <Play className="h-4 w-4" /> {loading ? "Analyzing Scenario..." : "Run What-If Analysis"}
              </Button>
            </div>
          </form>

          {/* Scenario Result Output */}
          {result && (
            <div className="mt-4 rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-5 space-y-4">
              <h4 className="text-sm font-bold text-white flex items-center justify-between">
                <span>Scenario Analysis Output</span>
                <Badge variant="emerald">Simulated</Badge>
              </h4>

              <p className="text-xs text-slate-200 font-mono bg-black/40 p-3 rounded-lg border border-white/5">
                {result.explanation}
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
                <div className="p-3 rounded-lg bg-black/40 border border-white/5">
                  <span className="text-slate-400 text-[10px] block">Analyzed Workload:</span>
                  <span className="text-white font-bold">{result.total_traces_analyzed} traces</span>
                </div>
                <div className="p-3 rounded-lg bg-black/40 border border-white/5">
                  <span className="text-slate-400 text-[10px] block">Rerouted / Blocked:</span>
                  <span className="text-cyan-300 font-bold">{result.rerouted_count}</span> / <span className="text-rose-400 font-bold">{result.blocked_count}</span>
                </div>
                <div className="p-3 rounded-lg bg-black/40 border border-white/5">
                  <span className="text-slate-400 text-[10px] block">Est. Cost Impact:</span>
                  <span className="text-emerald-400 font-bold">${result.cost_impact_usd.toFixed(4)}</span>
                </div>
                <div className="p-3 rounded-lg bg-black/40 border border-white/5">
                  <span className="text-slate-400 text-[10px] block">Latency Penalty:</span>
                  <span className="text-amber-300 font-bold">+{result.latency_impact_ms} ms</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
