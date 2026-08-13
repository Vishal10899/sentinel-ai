"use client";

import { useState } from "react";
import { Code2, Copy, Play, Check, Send, Sparkles, Terminal, FileCode, Layers } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, Toast } from "../../components/ui";
import { API_BASE_URL, api } from "../../lib/api";

const examples = {
  "GET /health": {
    method: "GET",
    path: "/health",
    description: "Ping core system health status",
    payload: null,
  },
  "GET /providers": {
    method: "GET",
    path: "/providers",
    description: "Fetch registered LLM provider adapters and readiness",
    payload: null,
  },
  "POST /routing/route": {
    method: "POST",
    path: "/routing/route",
    description: "Execute intelligent adaptive model selection",
    payload: {
      task_category: "chat",
      strategy: "balanced",
      max_cost_per_1k_tokens: 0.01,
      min_quality_score: 0.8,
    },
  },
  "POST /cost/compare": {
    method: "POST",
    path: "/cost/compare",
    description: "Calculate cost breakdown across all active models",
    payload: {
      input_tokens: 1000,
      output_tokens: 500,
    },
  },
};

export default function ApiPlayground() {
  const [selectedKey, setSelectedKey] = useState("POST /routing/route");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState("");
  const [copied, setCopied] = useState(false);

  const currentEndpoint = examples[selectedKey];

  const handleRunRequest = async () => {
    setLoading(true);
    setResponse(null);
    try {
      let res;
      if (selectedKey.includes("routing")) {
        res = await api.route(currentEndpoint.payload);
      } else if (selectedKey.includes("compare")) {
        res = await api.compare(currentEndpoint.payload);
      } else if (selectedKey.includes("providers")) {
        res = await api.providerHealth();
      } else {
        res = await api.health();
      }
      setResponse({ status: 200, data: res });
    } catch (e) {
      setResponse({ status: 500, error: e.message });
    } finally {
      setLoading(false);
    }
  };

  const handleCopyResponse = () => {
    if (!response) return;
    navigator.clipboard?.writeText(JSON.stringify(response, null, 2));
    setCopied(true);
    setToast("API response payload copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <AppShell>
      <div className="space-y-6 max-w-7xl mx-auto">
        <PageTitle
          eyebrow="Developer Tools"
          title="Interactive API REST Explorer"
          subtitle="Test live Control Plane endpoints, inspect JSON schemas, and measure request execution in real time."
          action={
            <Button variant="secondary" size="sm" onClick={() => window.open(`${API_BASE_URL.replace("/api/v1", "")}/docs`, "_blank")}>
              <Terminal className="h-3.5 w-3.5" /> Open OpenAPI Swagger Docs
            </Button>
          }
        />

        {toast && <Toast message={toast} onClose={() => setToast("")} />}

        <div className="grid gap-6 lg:grid-cols-5 items-start">
          {/* Endpoint Selector Sidebar */}
          <section className="surface p-4 lg:col-span-2 space-y-3">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)] block px-2">
              Available REST Endpoints
            </span>
            <div className="space-y-1">
              {Object.entries(examples).map(([key, item]) => {
                const isSelected = selectedKey === key;
                return (
                  <button
                    key={key}
                    onClick={() => {
                      setSelectedKey(key);
                      setResponse(null);
                    }}
                    className={`w-full rounded-xl p-3 text-left transition cursor-pointer flex items-center justify-between ${
                      isSelected
                        ? "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 font-semibold"
                        : "text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] border border-transparent"
                    }`}
                  >
                    <div className="space-y-0.5 min-w-0 pr-2">
                      <div className="flex items-center gap-2">
                        <Badge variant={item.method === "GET" ? "emerald" : "indigo"}>{item.method}</Badge>
                        <span className="font-mono text-xs truncate">{item.path}</span>
                      </div>
                      <p className="text-[11px] text-[var(--text-muted)] line-clamp-1">{item.description}</p>
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="border-t border-[var(--border-color)] pt-3 px-2">
              <span className="text-[11px] text-[var(--text-muted)] block">Base Target URL:</span>
              <code className="text-[10px] font-mono text-indigo-400 block mt-1 truncate">{API_BASE_URL}</code>
            </div>
          </section>

          {/* Request Payload & Response Inspector Panel */}
          <section className="surface p-6 lg:col-span-3 space-y-5">
            <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <Badge variant={currentEndpoint.method === "GET" ? "emerald" : "indigo"}>
                    {currentEndpoint.method}
                  </Badge>
                  <h3 className="text-sm font-mono font-bold text-[var(--text-primary)]">{currentEndpoint.path}</h3>
                </div>
                <p className="text-xs text-[var(--text-secondary)] mt-1">{currentEndpoint.description}</p>
              </div>

              <Button onClick={handleRunRequest} isLoading={loading}>
                <Play className="h-4 w-4" /> Run Request
              </Button>
            </div>

            {/* Request Body Code Block */}
            <div className="space-y-2">
              <span className="text-[11px] font-mono font-semibold text-[var(--text-muted)] uppercase tracking-wider block">
                Request JSON Payload
              </span>
              <div className="rounded-xl border border-slate-800 bg-[#0f172a] p-4 text-xs font-mono text-cyan-300 shadow-xl overflow-x-auto">
                <pre>{currentEndpoint.payload ? JSON.stringify(currentEndpoint.payload, null, 2) : "// No request body required for GET requests"}</pre>
              </div>
            </div>

            {/* Response Code Block */}
            <div className="space-y-2 pt-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono font-semibold text-[var(--text-muted)] uppercase tracking-wider block">
                  Response Payload Inspector
                </span>
                {response && (
                  <button
                    onClick={handleCopyResponse}
                    className="flex items-center gap-1 text-[11px] font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition cursor-pointer"
                  >
                    {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                    <span>{copied ? "Copied!" : "Copy JSON"}</span>
                  </button>
                )}
              </div>

              <div className="rounded-xl border border-slate-800 bg-[#0f172a] p-4 text-xs font-mono min-h-48 shadow-xl overflow-x-auto">
                {loading ? (
                  <div className="flex items-center gap-2 text-indigo-400">
                    <Sparkles className="h-4 w-4 animate-spin" />
                    <span>Executing HTTP request against Control Plane...</span>
                  </div>
                ) : response ? (
                  <pre className={response.status === 200 ? "text-emerald-300" : "text-rose-400"}>
                    {JSON.stringify(response.data || response.error, null, 2)}
                  </pre>
                ) : (
                  <span className="text-slate-500">// Click "Run Request" to execute endpoint and view live response payload.</span>
                )}
              </div>
            </div>
          </section>
        </div>
      </div>
    </AppShell>
  );
}
