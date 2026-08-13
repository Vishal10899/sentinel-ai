"use client";

import { useEffect, useState } from "react";
import { CircleDollarSign, TrendingUp, ShieldAlert, Zap, Sliders, RefreshCw, Layers, CheckCircle2, ArrowRight } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import { api } from "../../lib/api";

export default function FinOpsPage() {
  const [budget, setBudget] = useState(null);
  const [spend, setSpend] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [recs, setRecs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  const [activeTab, setActiveTab] = useState("overview"); // overview, explorer, optimization, config

  // Budget Configuration State
  const [monthlyLimit, setMonthlyLimit] = useState(500);
  const [actionOnExceeded, setActionOnExceeded] = useState("REJECT");

  const loadData = async () => {
    try {
      setLoading(true);
      const [budgetData, spendData, forecastData, alertsData, recsData] = await Promise.all([
        api.getBudgets("default"),
        api.getSpendSummary("default"),
        api.getForecast("default"),
        api.getFinOpsAlerts("default"),
        api.getCostOptimizations(),
      ]);

      setBudget(budgetData);
      setSpend(spendData);
      setForecast(forecastData);
      setAlerts(alertsData || []);
      setRecs(recsData || []);

      if (budgetData) {
        setMonthlyLimit(budgetData.monthly_budget_usd);
        setActionOnExceeded(budgetData.action_on_exceeded);
      }
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

  const handleSaveBudget = async (e) => {
    e.preventDefault();
    try {
      const updated = await api.updateBudget({
        workspace_id: "default",
        monthly_budget_usd: parseFloat(monthlyLimit),
        action_on_exceeded: actionOnExceeded,
      });
      setBudget(updated);
      setToast({ type: "success", message: "Workspace budget limit updated!" });
    } catch (err) {
      setToast({ type: "error", message: `Failed: ${err.message}` });
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageTitle
          title="Enterprise Financial Governance & Cost Center"
          subtitle="Real-time FinOps spend tracking, multi-tenant budget governance, EOM forecasting, and AI cost optimization recommendations."
          action={
            <Button variant="zinc" onClick={loadData}>
              <RefreshCw className="h-4 w-4" /> Refresh Spend Data
            </Button>
          }
        />

        {toast && <Toast type={toast.type} message={toast.message} onClose={() => setToast(null)} />}

        {loading ? (
          <LoadingCard title="Loading Financial Intelligence Data..." />
        ) : error ? (
          <ErrorCard title="FinOps Load Error" message={error} onRetry={loadData} />
        ) : (
          <>
            {/* Top Financial Overview Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl">
                <div className="flex items-center justify-between text-slate-400 text-xs">
                  <span>Current Spend</span>
                  <CircleDollarSign className="h-4 w-4 text-emerald-400" />
                </div>
                <p className="text-2xl font-extrabold text-white mt-2">${budget?.current_spend_usd?.toFixed(2) || "0.00"}</p>
                <p className="text-[11px] text-emerald-400 mt-1">{budget?.percentage_used}% of ${budget?.monthly_budget_usd} budget</p>
              </div>

              <div className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl">
                <div className="flex items-center justify-between text-slate-400 text-xs">
                  <span>Budget Remaining</span>
                  <Sliders className="h-4 w-4 text-indigo-400" />
                </div>
                <p className="text-2xl font-extrabold text-indigo-300 mt-2">${budget?.remaining_budget?.toFixed(2) || "0.00"}</p>
                <p className="text-[11px] text-slate-400 mt-1">Enforcement: {budget?.action_on_exceeded}</p>
              </div>

              <div className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl">
                <div className="flex items-center justify-between text-slate-400 text-xs">
                  <span>EOM Forecast</span>
                  <TrendingUp className="h-4 w-4 text-amber-400" />
                </div>
                <p className="text-2xl font-extrabold text-amber-300 mt-2">${forecast?.projected_monthly_spend_usd?.toFixed(2) || "0.00"}</p>
                <p className="text-[11px] text-amber-400 mt-1">
                  {forecast?.is_on_track ? "On Track with budget" : "Exhaustion Date: Day " + forecast?.budget_exhaustion_day}
                </p>
              </div>

              <div className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl">
                <div className="flex items-center justify-between text-slate-400 text-xs">
                  <span>Optimization Potential</span>
                  <Zap className="h-4 w-4 text-cyan-400" />
                </div>
                <p className="text-2xl font-extrabold text-cyan-300 mt-2">
                  ${recs.reduce((acc, r) => acc + r.estimated_monthly_savings_usd, 0).toFixed(2)}/mo
                </p>
                <p className="text-[11px] text-slate-400 mt-1">{recs.length} actionable suggestions</p>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b border-white/10 text-xs font-semibold gap-6">
              {[
                ["overview", "Overview & Forecast"],
                ["explorer", "Cost Explorer"],
                ["optimization", "AI Cost Optimization"],
                ["config", "Budget Configuration"],
              ].map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  className={`pb-3 transition ${activeTab === key ? "border-b-2 border-indigo-500 text-indigo-400" : "text-slate-400 hover:text-white"}`}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Tab 1: Overview & Forecast */}
            {activeTab === "overview" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-amber-400" /> End-of-Month Spend Projection
                  </h3>
                  <div className="rounded-xl border border-white/10 bg-black/40 p-4 space-y-3 text-xs">
                    <div className="flex justify-between text-slate-300">
                      <span>Daily Run Rate:</span>
                      <span className="font-mono text-white font-bold">${forecast?.daily_run_rate_usd?.toFixed(2)} / day</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Monthly Budget:</span>
                      <span className="font-mono text-white font-bold">${forecast?.monthly_budget_usd?.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Projected End-of-Month:</span>
                      <span className={`font-mono font-bold ${forecast?.is_on_track ? "text-emerald-400" : "text-rose-400"}`}>
                        ${forecast?.projected_monthly_spend_usd?.toFixed(2)}
                      </span>
                    </div>

                    <div className="pt-2 border-t border-white/10">
                      <span className="text-[11px] text-slate-400 block mb-1">Budget Burn Progress:</span>
                      <div className="h-3 rounded-full bg-white/10 overflow-hidden">
                        <div
                          className={`h-full ${budget?.percentage_used >= 90 ? "bg-rose-500" : budget?.percentage_used >= 75 ? "bg-amber-500" : "bg-emerald-500"}`}
                          style={{ width: `${Math.min(budget?.percentage_used || 0, 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4 text-rose-400" /> Active Threshold Alerts
                  </h3>
                  <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                    {alerts.length === 0 ? (
                      <p className="text-xs text-slate-500 p-4 text-center">No budget threshold alerts triggered.</p>
                    ) : (
                      alerts.map((a) => (
                        <div key={a.id} className="rounded-xl border border-white/10 bg-black/40 p-3 flex items-start justify-between text-xs">
                          <div>
                            <p className="font-semibold text-white">{a.message}</p>
                            <span className="text-[10px] text-slate-400">{new Date(a.timestamp * 1000).toLocaleString()}</span>
                          </div>
                          <Badge variant={a.severity === "CRITICAL" ? "rose" : "amber"}>{a.severity}</Badge>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: Cost Explorer */}
            {activeTab === "explorer" && spend && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
                  <h3 className="text-sm font-bold text-white">Spend by AI Provider</h3>
                  <div className="space-y-2">
                    {Object.entries(spend.spend_by_provider || {}).length === 0 ? (
                      <p className="text-xs text-slate-500">No provider transactions recorded.</p>
                    ) : (
                      Object.entries(spend.spend_by_provider).map(([prov, amt]) => (
                        <div key={prov} className="flex justify-between items-center text-xs p-2.5 rounded-lg bg-black/40 border border-white/5">
                          <span className="font-semibold text-white uppercase">{prov}</span>
                          <span className="font-mono text-emerald-400 font-bold">${amt.toFixed(4)}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                <div className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl space-y-4">
                  <h3 className="text-sm font-bold text-white">Spend by LLM Model</h3>
                  <div className="space-y-2">
                    {Object.entries(spend.spend_by_model || {}).length === 0 ? (
                      <p className="text-xs text-slate-500">No model transactions recorded.</p>
                    ) : (
                      Object.entries(spend.spend_by_model).map(([mod, amt]) => (
                        <div key={mod} className="flex justify-between items-center text-xs p-2.5 rounded-lg bg-black/40 border border-white/5">
                          <span className="font-mono text-indigo-300">{mod}</span>
                          <span className="font-mono text-emerald-400 font-bold">${amt.toFixed(4)}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Tab 3: AI Cost Optimization */}
            {activeTab === "optimization" && (
              <div className="space-y-4">
                {recs.map((r) => (
                  <div key={r.id} className="surface rounded-2xl border border-white/10 p-5 bg-[#111827] shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-sm">{r.title}</span>
                        <Badge variant="cyan">{r.category}</Badge>
                      </div>
                      <p className="text-xs text-slate-300">{r.suggestion}</p>
                    </div>

                    <div className="flex items-center gap-4 shrink-0">
                      <div className="text-right">
                        <span className="text-xs text-slate-400 block">Estimated Savings:</span>
                        <span className="font-mono font-extrabold text-emerald-400 text-base">
                          ${r.estimated_monthly_savings_usd}/mo ({r.savings_percentage}%)
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Tab 4: Budget Configuration */}
            {activeTab === "config" && (
              <form onSubmit={handleSaveBudget} className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl max-w-xl space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Sliders className="h-4 w-4 text-indigo-400" /> Workspace Budget Controls
                </h3>

                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Monthly Budget ($ USD)</label>
                  <input
                    type="number"
                    step="50"
                    required
                    value={monthlyLimit}
                    onChange={(e) => setMonthlyLimit(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Action on Limit Exceeded</label>
                  <select
                    value={actionOnExceeded}
                    onChange={(e) => setActionOnExceeded(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                  >
                    <option value="REJECT">REJECT (Block requests with HTTP 403)</option>
                    <option value="WARN">WARN (Allow requests with warning header)</option>
                    <option value="DOWNGRADE_MODEL">DOWNGRADE_MODEL (Route requests to lowest-cost model)</option>
                  </select>
                </div>

                <Button type="submit">Save Budget Governance</Button>
              </form>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}
