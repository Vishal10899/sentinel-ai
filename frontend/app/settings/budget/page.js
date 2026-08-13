"use client";

import { useEffect, useState } from "react";
import { CircleDollarSign, AlertCircle, Save, CheckCircle, RefreshCw } from "lucide-react";
import { AppShell, PageTitle } from "../../../components/shell";
import { Button, Toast } from "../../../components/ui";
import WithAdminAuth from "../../../components/WithAdminAuth";
import api from "../../../lib/api";

function WorkspaceBudgetPage() {
  const [budgetCap, setBudgetCap] = useState("5000");
  const [alertThreshold, setAlertThreshold] = useState("80");
  const [currentUsage, setCurrentUsage] = useState("1240.50");
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState("");

  const handleSave = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setToast("Global Workspace Budget Caps saved successfully.");
    }, 400);
  };

  return (
    <AppShell
      title="Workspace Budget Caps"
      subtitle="Enforce financial controls, spending limits, & alerting thresholds across LLM providers"
    >
      <PageTitle
        eyebrow="FinOps & Cost Control"
        title="Global Workspace Budget Caps"
        subtitle="Configure monthly spend limits, rate caps, and auto-throttling rules."
      />

      <div className="max-w-3xl space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="surface p-5 border border-[var(--border-color)] rounded-2xl">
            <p className="text-xs text-slate-400 font-medium">Monthly Spend Cap</p>
            <p className="text-3xl font-extrabold text-white mt-1">${budgetCap}.00</p>
            <p className="text-[11px] text-emerald-400 mt-2 flex items-center gap-1">
              <CheckCircle className="h-3 w-3" /> Hard Cap Active
            </p>
          </div>

          <div className="surface p-5 border border-[var(--border-color)] rounded-2xl">
            <p className="text-xs text-slate-400 font-medium">Current Month Usage</p>
            <p className="text-3xl font-extrabold text-indigo-400 mt-1">${currentUsage}</p>
            <div className="w-full bg-white/10 h-2 rounded-full mt-3 overflow-hidden">
              <div className="bg-indigo-500 h-full rounded-full" style={{ width: `${(parseFloat(currentUsage) / parseFloat(budgetCap)) * 100}%` }} />
            </div>
          </div>
        </div>

        <div className="surface p-6 border border-[var(--border-color)] rounded-2xl space-y-5">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Budget Settings</h3>

          <div className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Monthly Maximum Budget Cap ($ USD)</label>
              <input
                type="number"
                value={budgetCap}
                onChange={(e) => setBudgetCap(e.target.value)}
                className="w-full rounded-xl bg-black/40 px-3.5 py-2.5 text-sm text-white border border-white/10 outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">Alert Threshold (% of Cap)</label>
              <input
                type="number"
                value={alertThreshold}
                onChange={(e) => setAlertThreshold(e.target.value)}
                className="w-full rounded-xl bg-black/40 px-3.5 py-2.5 text-sm text-white border border-white/10 outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-white/10 flex justify-end">
            <Button onClick={handleSave} disabled={loading}>
              <Save className="h-4 w-4" /> {loading ? "Saving..." : "Save Budget Caps"}
            </Button>
          </div>
        </div>
      </div>

      {toast && <Toast message={toast} clear={() => setToast("")} />}
    </AppShell>
  );
}

export default WithAdminAuth(WorkspaceBudgetPage);
