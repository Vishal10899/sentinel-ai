"use client";

import { useState } from "react";
import { Check, Moon, Save, Server, Sun, ShieldCheck, Database, Bell, Sliders } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, Toast } from "../../components/ui";
import { useTheme } from "../../providers/ThemeProvider";
import { API_BASE_URL } from "../../lib/api";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [toast, setToast] = useState("");
  const [telemetryEnabled, setTelemetryEnabled] = useState(true);
  const [autoCacheEnabled, setAutoCacheEnabled] = useState(true);
  const [piiFilteringEnabled, setPiiFilteringEnabled] = useState(true);

  const handleSave = () => {
    setToast("Control plane settings saved successfully!");
  };

  return (
    <AppShell>
      <div className="space-y-6 max-w-5xl mx-auto">
        <PageTitle
          eyebrow="Workspace Configuration"
          title="Console & Control Plane Settings"
          subtitle="Configure interface appearance, global AI guardrails, API proxy preferences, and telemetry options."
          action={
            <Button onClick={handleSave} size="sm">
              <Save className="h-3.5 w-3.5" /> Save Preferences
            </Button>
          }
        />

        {toast && <Toast message={toast} onClose={() => setToast("")} />}

        <div className="space-y-6">
          {/* Section 1: Appearance & Theme Mode */}
          <section className="surface p-6 space-y-4">
            <div className="flex items-center gap-3 border-b border-[var(--border-color)] pb-3">
              <div className="rounded-xl bg-indigo-500/10 border border-indigo-500/20 p-2 text-indigo-400">
                <Sun className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-[var(--text-primary)]">Interface Theme Mode</h3>
                <p className="text-xs text-[var(--text-secondary)]">Customize interface color scheme across all Sentinel pages.</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
              <button
                onClick={() => setTheme("dark")}
                className={`p-4 rounded-2xl border text-left transition cursor-pointer flex flex-col justify-between h-28 ${
                  theme === "dark"
                    ? "border-indigo-500 bg-indigo-500/10 ring-2 ring-indigo-500/20"
                    : "border-[var(--border-color)] bg-[var(--bg-secondary)] hover:border-[var(--border-hover)]"
                }`}
              >
                <div className="flex items-center justify-between">
                  <Moon className="h-5 w-5 text-indigo-400" />
                  {theme === "dark" && <Check className="h-4 w-4 text-indigo-400" />}
                </div>
                <div>
                  <p className="text-xs font-bold text-[var(--text-primary)]">Dark Mode</p>
                  <p className="text-[11px] text-[var(--text-secondary)]">Midnight slate theme</p>
                </div>
              </button>

              <button
                onClick={() => setTheme("light")}
                className={`p-4 rounded-2xl border text-left transition cursor-pointer flex flex-col justify-between h-28 ${
                  theme === "light"
                    ? "border-indigo-500 bg-indigo-500/10 ring-2 ring-indigo-500/20"
                    : "border-[var(--border-color)] bg-[var(--bg-secondary)] hover:border-[var(--border-hover)]"
                }`}
              >
                <div className="flex items-center justify-between">
                  <Sun className="h-5 w-5 text-amber-500" />
                  {theme === "light" && <Check className="h-4 w-4 text-indigo-500" />}
                </div>
                <div>
                  <p className="text-xs font-bold text-[var(--text-primary)]">Light Mode</p>
                  <p className="text-[11px] text-[var(--text-secondary)]">Layered slate-tinted canvas</p>
                </div>
              </button>

              <button
                onClick={() => setTheme("system")}
                className={`p-4 rounded-2xl border text-left transition cursor-pointer flex flex-col justify-between h-28 ${
                  theme === "system"
                    ? "border-indigo-500 bg-indigo-500/10 ring-2 ring-indigo-500/20"
                    : "border-[var(--border-color)] bg-[var(--bg-secondary)] hover:border-[var(--border-hover)]"
                }`}
              >
                <div className="flex items-center justify-between">
                  <Sliders className="h-5 w-5 text-purple-400" />
                  {theme === "system" && <Check className="h-4 w-4 text-indigo-400" />}
                </div>
                <div>
                  <p className="text-xs font-bold text-[var(--text-primary)]">System Preference</p>
                  <p className="text-[11px] text-[var(--text-secondary)]">Sync with OS settings</p>
                </div>
              </button>
            </div>
          </section>

          {/* Section 2: API Gateway & Base URL */}
          <section className="surface p-6 space-y-4">
            <div className="flex items-center gap-3 border-b border-[var(--border-color)] pb-3">
              <div className="rounded-xl bg-cyan-500/10 border border-cyan-500/20 p-2 text-cyan-400">
                <Server className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-[var(--text-primary)]">Backend API Gateway URL</h3>
                <p className="text-xs text-[var(--text-secondary)]">Active REST API target for the Sentinel Control Plane.</p>
              </div>
            </div>

            <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-4 space-y-2">
              <span className="text-[11px] font-mono text-[var(--text-muted)] block">Configured Environment Variable:</span>
              <code className="text-xs font-mono text-cyan-400 block font-bold">{API_BASE_URL}</code>
            </div>
          </section>

          {/* Section 3: Guardrail & Cache System Toggles */}
          <section className="surface p-6 space-y-4">
            <div className="flex items-center gap-3 border-b border-[var(--border-color)] pb-3">
              <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-2 text-emerald-400">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-[var(--text-primary)]">Security & Performance Defaults</h3>
                <p className="text-xs text-[var(--text-secondary)]">Configure default interception and caching policies.</p>
              </div>
            </div>

            <div className="space-y-3 pt-1">
              <div className="flex items-center justify-between p-3.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                <div>
                  <p className="text-xs font-bold text-[var(--text-primary)]">Automatic PII & Secret Redaction</p>
                  <p className="text-[11px] text-[var(--text-secondary)]">Intercept SSNs, Credit Cards, and API Keys before sending to LLM providers.</p>
                </div>
                <input
                  type="checkbox"
                  checked={piiFilteringEnabled}
                  onChange={(e) => setPiiFilteringEnabled(e.target.checked)}
                  className="h-4 w-4 rounded border-[var(--border-color)] text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                />
              </div>

              <div className="flex items-center justify-between p-3.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                <div>
                  <p className="text-xs font-bold text-[var(--text-primary)]">Semantic Prompt Cache</p>
                  <p className="text-[11px] text-[var(--text-secondary)]">Serve sub-10ms cached answers for duplicate prompt requests.</p>
                </div>
                <input
                  type="checkbox"
                  checked={autoCacheEnabled}
                  onChange={(e) => setAutoCacheEnabled(e.target.checked)}
                  className="h-4 w-4 rounded border-[var(--border-color)] text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                />
              </div>

              <div className="flex items-center justify-between p-3.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                <div>
                  <p className="text-xs font-bold text-[var(--text-primary)]">Distributed OpenTelemetry Tracing</p>
                  <p className="text-[11px] text-[var(--text-secondary)]">Emit P95 latency logs and step execution profiles to Observability timeline.</p>
                </div>
                <input
                  type="checkbox"
                  checked={telemetryEnabled}
                  onChange={(e) => setTelemetryEnabled(e.target.checked)}
                  className="h-4 w-4 rounded border-[var(--border-color)] text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                />
              </div>
            </div>
          </section>
        </div>
      </div>
    </AppShell>
  );
}
