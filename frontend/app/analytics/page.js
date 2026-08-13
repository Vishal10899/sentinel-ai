"use client";

import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Calculator, Coins, Trophy, TrendingDown, DollarSign, AlertCircle, ShieldAlert, Sparkles, RefreshCw } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import { api } from "../../lib/api";

export default function Analytics() {
  const [models, setModels] = useState(null);
  const [selected, setSelected] = useState("openai/gpt-4o-mini");
  const [input, setInput] = useState(1000);
  const [output, setOutput] = useState(500);
  const [estimate, setEstimate] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [budget, setBudget] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [mounted, setMounted] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setMounted(true);
  }, []);

  const loadData = () => {
    setError("");
    setLoading(true);
    Promise.all([api.models(), api.getBudget(), api.getRecommendations()])
      .then(([modelList, budgetData, recData]) => {
        setModels(modelList || []);
        setBudget(budgetData);
        setRecommendations(recData || []);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(loadData, []);

  const choice = selected ? selected.split("/") : ["openai", "gpt-4o-mini"];

  const calculate = async () => {
    setError("");
    try {
      const p = {
        provider_id: choice[0] || "openai",
        model_id: choice[1] || "gpt-4o-mini",
        input_tokens: +input || 1000,
        output_tokens: +output || 500,
      };
      const [a, b] = await Promise.all([
        api.estimate(p),
        api.compare({ input_tokens: +input || 1000, output_tokens: +output || 500 }),
      ]);
      setEstimate(a);
      setComparison(b);
    } catch (e) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (models && models.length > 0) calculate();
  }, [models]);

  const chart = useMemo(
    () =>
      comparison?.estimates?.map((x) => ({
        name: x.model_id,
        cost: Number(x.estimated_cost_usd),
      })) || [],
    [comparison]
  );

  return (
    <AppShell>
      <PageTitle
        eyebrow="Financial Governance & Intelligence"
        title="Cost Analytics & Forecast Engine"
        subtitle="Live token pricing calculator, workspace spend caps, and AI-driven model cost optimizations."
        action={
          <Button variant="secondary" size="sm" onClick={loadData} isLoading={loading}>
            <RefreshCw className="h-3.5 w-3.5" /> Refresh Analytics
          </Button>
        }
      />

      {error ? (
        <ErrorCard title="Analytics Telemetry Error" message={error} onRetry={calculate} />
      ) : !models || loading ? (
        <LoadingCard label="Loading Cost Intelligence Engine..." />
      ) : (
        <>
          {/* Workspace Budget Tracker */}
          {budget && (
            <div className="surface mb-6 p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="grid h-10 w-10 place-items-center rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                  <DollarSign className="h-5 w-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-white">Workspace Budget Enforcer</h3>
                    <Badge tone={budget.warning_status === "normal" ? "green" : "amber"}>
                      {budget.warning_status ? budget.warning_status.toUpperCase() : "NORMAL"}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5 font-mono">
                    Monthly Limit: <span className="text-white font-medium">${budget.monthly_budget_usd}</span> · Current Spend: <span className="text-emerald-400 font-medium">${budget.current_spend_usd}</span>
                  </p>
                </div>
              </div>

              <div className="w-full md:w-64">
                <div className="flex justify-between text-xs mb-1 font-mono">
                  <span className="text-slate-400">Budget Utilized</span>
                  <span className="font-semibold text-indigo-300">{budget.percentage_used}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-black/40 border border-white/10 overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      budget.percentage_used >= 90 ? "bg-rose-500" : budget.percentage_used >= 80 ? "bg-amber-500" : "bg-indigo-500"
                    }`}
                    style={{ width: `${Math.min(budget.percentage_used || 0, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Main Grid: Calculator, Comparison, Recommendations */}
          <div className="grid gap-5 xl:grid-cols-3">
            {/* Cost Calculator */}
            <section className="surface p-5 xl:col-span-1 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 border-b border-white/[0.08] pb-3 mb-4">
                  <Calculator className="h-4 w-4 text-indigo-400" />
                  <h3 className="font-bold text-sm text-white">Live Cost Estimator</h3>
                </div>

                <label className="block text-xs font-semibold text-slate-300">
                  Target Model
                  <select
                    value={selected}
                    onChange={(e) => setSelected(e.target.value)}
                    className="mt-1.5 w-full rounded-xl border border-white/10 bg-black/40 p-2.5 text-xs text-white outline-none focus:border-indigo-500 font-mono"
                  >
                    {models.map((m) => (
                      <option value={`${m.provider_id}/${m.model_id}`} key={m.model_id}>
                        {m.display_name} ({m.provider_id})
                      </option>
                    ))}
                  </select>
                </label>

                <div className="mt-4 grid grid-cols-2 gap-3">
                  <label className="text-xs font-semibold text-slate-300">
                    Input Tokens
                    <input
                      type="number"
                      min="0"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      className="mt-1.5 w-full rounded-xl border border-white/10 bg-black/40 p-2.5 text-xs text-white outline-none font-mono"
                    />
                  </label>
                  <label className="text-xs font-semibold text-slate-300">
                    Output Tokens
                    <input
                      type="number"
                      min="0"
                      value={output}
                      onChange={(e) => setOutput(e.target.value)}
                      className="mt-1.5 w-full rounded-xl border border-white/10 bg-black/40 p-2.5 text-xs text-white outline-none font-mono"
                    />
                  </label>
                </div>

                <Button className="mt-5 w-full" onClick={calculate}>
                  Recalculate Estimates
                </Button>
              </div>

              {estimate && (
                <div className="mt-5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 p-4 space-y-3">
                  <div>
                    <p className="text-[11px] font-mono text-indigo-300">Per-Request Cost</p>
                    <p className="mt-0.5 text-xl font-bold text-emerald-400 font-mono">
                      ${estimate.estimated_cost_usd}
                    </p>
                  </div>
                  <div className="pt-2 border-t border-white/10 grid grid-cols-2 gap-2 text-xs font-mono">
                    <div>
                      <p className="text-slate-400 text-[10px]">Daily Forecast</p>
                      <p className="font-semibold text-white">${estimate.daily_forecast_usd}</p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-[10px]">Monthly Forecast</p>
                      <p className="font-semibold text-white">${estimate.monthly_forecast_usd}</p>
                    </div>
                  </div>
                </div>
              )}
            </section>

            {/* Catalog Comparison */}
            <section className="surface p-5 xl:col-span-2">
              <div className="flex items-start justify-between border-b border-white/[0.08] pb-3 mb-4">
                <div>
                  <h3 className="font-bold text-sm text-white">Catalog Model Pricing Matrix</h3>
                  <p className="mt-0.5 text-xs text-slate-400 font-mono">
                    Simulated workload: {input} prompt tokens, {output} completion tokens
                  </p>
                </div>
                {comparison?.cheapest && (
                  <Badge tone="green">
                    <Trophy className="h-3.5 w-3.5" /> Best Value: {comparison.cheapest.model_id}
                  </Badge>
                )}
              </div>

              {comparison ? (
                <>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-xl bg-white/[0.02] p-3.5 border border-white/5">
                      <p className="text-[11px] text-slate-400">Lowest Cost Model</p>
                      <p className="mt-1 truncate font-bold text-xs text-white font-mono">{comparison.cheapest?.model_id}</p>
                      <p className="mt-0.5 text-sm text-emerald-400 font-mono">${comparison.cheapest?.estimated_cost_usd}</p>
                    </div>

                    <div className="rounded-xl bg-white/[0.02] p-3.5 border border-white/5">
                      <p className="text-[11px] text-slate-400">Highest Cost Model</p>
                      <p className="mt-1 truncate font-bold text-xs text-white font-mono">{comparison.most_expensive?.model_id}</p>
                      <p className="mt-0.5 text-sm text-rose-400 font-mono">${comparison.most_expensive?.estimated_cost_usd}</p>
                    </div>

                    <div className="rounded-xl bg-indigo-500/10 p-3.5 border border-indigo-500/20">
                      <p className="text-[11px] text-indigo-300">Max Optimization Savings</p>
                      <p className="mt-1 truncate font-bold text-xs text-white font-mono">
                        {Number(comparison.savings_percentage || 0).toFixed(1)}%
                      </p>
                      <p className="mt-0.5 text-sm text-emerald-400 font-mono">
                        ${comparison.savings_amount_usd} / req
                      </p>
                    </div>
                  </div>

                  {/* Recharts Bar Chart */}
                  <div className="mt-5 h-60 w-full">
                    {mounted ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chart}>
                          <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                          <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                          <Tooltip contentStyle={{ background: '#0c1017', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, fontSize: 12 }} />
                          <Bar dataKey="cost" fill="#6366f1" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full w-full bg-white/[0.02] rounded-xl animate-pulse" />
                    )}
                  </div>
                </>
              ) : (
                <LoadingCard label="Evaluating catalog tariffs..." />
              )}
            </section>
          </div>

          {/* AI Cost Optimization Recommendations */}
          <section className="surface mt-6 p-5">
            <div className="flex items-center gap-2 border-b border-white/[0.08] pb-3 mb-4">
              <Sparkles className="h-4 w-4 text-amber-400" />
              <h3 className="font-bold text-sm text-white">AI Cost Optimization Recommendations</h3>
            </div>

            {recommendations.length === 0 ? (
              <p className="text-xs text-slate-400 p-4">No active optimization recommendations currently required for this workload.</p>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {recommendations.map((rec, idx) => (
                  <div key={idx} className="rounded-xl bg-white/[0.02] border border-white/10 p-4 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-white font-mono">{rec.current_model} → {rec.recommended_model}</span>
                        <Badge tone="green">{Number(rec.savings_percentage || 0).toFixed(1)}% Savings</Badge>
                      </div>
                      <p className="mt-2 text-xs text-slate-300 leading-relaxed">{rec.suggestion_text}</p>
                    </div>
                    <div className="mt-3 pt-2 border-t border-white/[0.06] flex justify-between items-center text-xs font-mono">
                      <span className="text-slate-400">Est. savings per request</span>
                      <span className="text-emerald-400 font-bold">${rec.savings_amount_usd}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <Toast message={toast} clear={() => setToast("")} />
        </>
      )}
    </AppShell>
  );
}
