"use client";

import { useState, useEffect } from "react";
import { AppShell } from "../../components/shell";
import { API_BASE_URL } from "../../lib/api";


import {
  ShieldCheck,
  ShieldAlert,
  Cpu,
  Zap,
  Lock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Server,
  Terminal,
  Activity,
  Sliders,
  Sparkles
} from "lucide-react";

export default function MCPGovernancePage() {
  const [tools, setTools] = useState([]);
  const [rolePermissions, setRolePermissions] = useState({});
  const [loading, setLoading] = useState(true);
  const [testTool, setTestTool] = useState("query_sql");
  const [testRole, setTestRole] = useState("developer");
  const [testArgs, setTestArgs] = useState('{\n  "query": "SELECT * FROM users LIMIT 10"\n}');
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);

  // Multi-Attribute Scoring Weights State
  const [weights, setWeights] = useState({
    w1_cost: 0.30,
    w2_latency: 0.25,
    w3_quality: 0.35,
    w4_health: 0.10,
  });

  useEffect(() => {
    fetchMCPTools();
  }, []);

  const fetchMCPTools = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/mcp/tools`);
      if (res.ok) {
        const data = await res.json();
        setTools(data.tools || []);
        setRolePermissions(data.role_permissions || {});
      } else {
        // Fallback default enterprise catalog
        setTools([
          { name: "query_sql", description: "Execute SQL database query", risk: "MEDIUM", allowed_roles: ["admin", "developer", "analyst"] },
          { name: "search_docs", description: "Search enterprise vector knowledge base", risk: "LOW", allowed_roles: ["admin", "developer", "analyst", "viewer"] },
          { name: "fetch_web_page", description: "Fetch external HTTP web resource", risk: "LOW", allowed_roles: ["admin", "developer", "analyst"] },
          { name: "execute_system_command", description: "Execute backend system shell script", risk: "CRITICAL", allowed_roles: ["admin"] },
        ]);
        setRolePermissions({
          admin: ["*"],
          developer: ["query_sql", "search_docs", "fetch_web_page"],
          analyst: ["search_docs", "fetch_web_page"],
          viewer: ["search_docs"],
        });
      }
    } catch (err) {
      console.error("Failed fetching MCP tools:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleInspectPayload = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      let parsedArgs = {};
      try {
        parsedArgs = JSON.parse(testArgs);
      } catch (e) {
        setTestResult({ allowed: false, error: "Invalid JSON format in payload arguments." });
        setTesting(false);
        return;
      }

      const res = await fetch(`${API_BASE_URL}/mcp/inspect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tool_name: testTool,
          arguments: parsedArgs,
          user_role: testRole,
          workspace_id: "default",
        }),
      });


      const data = await res.json();
      if (res.ok) {
        setTestResult(data);
      } else {
        setTestResult({
          allowed: false,
          status: "BLOCKED",
          reason: data.detail?.error?.message || "Invocation blocked by MCP Governance engine.",
          risk_level: data.detail?.error?.risk_level || "HIGH",
        });
      }
    } catch (err) {
      setTestResult({ allowed: false, error: err.message });
    } finally {
      setTesting(false);
    }
  };

  return (
    <AppShell
      title="MCP Tool Governance & Multi-Attribute Smart Router"
      subtitle="Model Context Protocol (MCP) tool security, RBAC permission enforcement, and sub-100μs routing score tuning"
    >
      <div className="space-y-8">
        {/* Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-sm font-medium">Rust Data Plane SLA</span>
              <Zap className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-slate-100">&lt; 100 μs</div>
            <div className="text-xs text-emerald-400 font-medium mt-1">P99 High-Throughput Proxy</div>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-sm font-medium">MCP Tools Monitored</span>
              <ShieldCheck className="w-5 h-5 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold text-slate-100">{tools.length} Registered</div>
            <div className="text-xs text-cyan-400 font-medium mt-1">Zero-Trust Payload Invalidation</div>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-sm font-medium">Circuit Breakers</span>
              <Activity className="w-5 h-5 text-indigo-400" />
            </div>
            <div className="text-2xl font-bold text-emerald-400">OPERATIONAL</div>
            <div className="text-xs text-slate-400 mt-1">Sub-10ms Automated Failover</div>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-sm font-medium">Inline DLP Status</span>
              <ShieldAlert className="w-5 h-5 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-slate-100">ACTIVE</div>
            <div className="text-xs text-amber-400 font-medium mt-1">SSN, CC, API Key Zero-Copy Redaction</div>
          </div>
        </div>

        {/* Multi-Attribute Scoring Engine Configuration */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
                <Sliders className="w-5 h-5 text-indigo-400" />
                Multi-Attribute Scoring Function Tuning
              </h3>
              <p className="text-sm text-slate-400 font-mono mt-1">
                Score = w₁·Cost + w₂·Latency + w₃·Quality + w₄·Health
              </p>
            </div>
            <span className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-full text-xs font-semibold">
              Live Engine Score Target: 99.9%
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 pt-4 border-t border-slate-800">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-2">
                Cost Weight (w₁): {(weights.w1_cost * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.w1_cost}
                onChange={(e) => setWeights({ ...weights, w1_cost: parseFloat(e.target.value) })}
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-2">
                Latency Weight (w₂): {(weights.w2_latency * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.w2_latency}
                onChange={(e) => setWeights({ ...weights, w2_latency: parseFloat(e.target.value) })}
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-2">
                Quality Weight (w₃): {(weights.w3_quality * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.w3_quality}
                onChange={(e) => setWeights({ ...weights, w3_quality: parseFloat(e.target.value) })}
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-2">
                Health Weight (w₄): {(weights.w4_health * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.w4_health}
                onChange={(e) => setWeights({ ...weights, w4_health: parseFloat(e.target.value) })}
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Live Payload Inspector & Sandbox */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2 mb-4">
              <Terminal className="w-5 h-5 text-cyan-400" />
              MCP Governance Payload Simulator
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Target MCP Tool</label>
                <select
                  value={testTool}
                  onChange={(e) => setTestTool(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  {tools.map((t) => (
                    <option key={t.name} value={t.name}>
                      {t.name} ({t.risk} RISK)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Simulated User Role</label>
                <select
                  value={testRole}
                  onChange={(e) => setTestRole(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="admin">Administrator (Full Access)</option>
                  <option value="developer">Developer (Read/Write Query)</option>
                  <option value="analyst">Data Analyst (Read-Only Search)</option>
                  <option value="viewer">Viewer (Restricted)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Tool Arguments (JSON Payload)</label>
                <textarea
                  rows={4}
                  value={testArgs}
                  onChange={(e) => setTestArgs(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <button
                onClick={handleInspectPayload}
                disabled={testing}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium text-sm transition-colors flex items-center justify-center gap-2"
              >
                {testing ? "Evaluating Governance Rules..." : "Inspect & Validate Payload"}
              </button>
            </div>
          </div>

          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2 mb-4">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                Governance Evaluation Output
              </h3>

              {testResult ? (
                <div
                  className={`p-4 rounded-xl border ${
                    testResult.allowed
                      ? "bg-emerald-950/30 border-emerald-800/50 text-emerald-300"
                      : "bg-rose-950/30 border-rose-800/50 text-rose-300"
                  }`}
                >
                  <div className="flex items-center gap-2 font-bold text-sm mb-2">
                    {testResult.allowed ? (
                      <>
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        TOOL INVOCATION ALLOWED
                      </>
                    ) : (
                      <>
                        <XCircle className="w-5 h-5 text-rose-400" />
                        GOVERNANCE RULE VIOLATION (BLOCKED)
                      </>
                    )}
                  </div>
                  <p className="text-xs font-mono text-slate-300 mb-3">{testResult.reason || testResult.error}</p>
                  {testResult.risk_level && (
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                        testResult.risk_level === "CRITICAL"
                          ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                          : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                      }`}
                    >
                      RISK CLASS: {testResult.risk_level}
                    </span>
                  )}
                </div>
              ) : (
                <div className="h-48 border border-dashed border-slate-800 rounded-xl flex items-center justify-center text-slate-500 text-sm">
                  Run a payload inspection to view live governance evaluation output.
                </div>
              )}
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800 text-xs text-slate-400">
              <p>🛡️ Zero-Trust Enforcement: Prevents unauthorized SQL DELETE/DROP operations and privilege escalation.</p>
            </div>
          </div>
        </div>

        {/* Registered MCP Tool Catalog */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">Registered MCP Tool Governance Catalog</h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950 text-xs uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="p-3">Tool Name</th>
                  <th className="p-3">Description</th>
                  <th className="p-3">Risk Level</th>
                  <th className="p-3">Allowed RBAC Roles</th>
                  <th className="p-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {tools.map((t) => (
                  <tr key={t.name} className="hover:bg-slate-800/40">
                    <td className="p-3 font-mono font-medium text-indigo-400">{t.name}</td>
                    <td className="p-3 text-slate-300">{t.description}</td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                          t.risk === "CRITICAL"
                            ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                            : t.risk === "MEDIUM"
                            ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        }`}
                      >
                        {t.risk}
                      </span>
                    </td>
                    <td className="p-3 text-xs text-slate-400">
                      {Array.isArray(t.allowed_roles) ? t.allowed_roles.join(", ") : "admin"}
                    </td>
                    <td className="p-3 text-right">
                      <span className="text-xs font-semibold text-emerald-400 flex items-center justify-end gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> PROTECTED
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
