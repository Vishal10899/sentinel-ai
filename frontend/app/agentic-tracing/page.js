"use client";

import { useState } from "react";
import { AppShell } from "../../components/shell";
import {
  Sparkles,
  GitCommit,
  Activity,
  CheckCircle2,
  Clock,
  Layers,
  Terminal,
  ChevronRight,
  Server
} from "lucide-react";

export default function AgenticTracingPage() {
  const [selectedTrace, setSelectedTrace] = useState("trace-9942a8b");

  const [traces] = useState([
    {
      id: "trace-9942a8b",
      agent: "Multi-Agent Code Architect",
      timestamp: "2 minutes ago",
      duration_ms: 842,
      total_tokens: 1420,
      cost_usd: 0.0034,
      spans: [
        { name: "Intent Analysis & Intent Profiling", duration_ms: 1.2, status: "OK", type: "CONTROL_PLANE" },
        { name: "Multi-Attribute Router Candidate Scoring", duration_ms: 3.4, status: "OK", type: "ROUTER" },
        { name: "Rust Data Plane Zero-Copy DLP Inspection", duration_ms: 0.08, status: "OK", type: "DATA_PLANE" },
        { name: "MCP Governance Payload Safety Check (query_sql)", duration_ms: 2.1, status: "OK", type: "MCP_GOVERNANCE" },
        { name: "LLM Backend Execution (claude-3-5-sonnet)", duration_ms: 835.0, status: "OK", type: "PROVIDER_LLM" },
      ],
    },
    {
      id: "trace-7721f4c",
      agent: "FinOps Cost Guard Agent",
      timestamp: "8 minutes ago",
      duration_ms: 195,
      total_tokens: 410,
      cost_usd: 0.0008,
      spans: [
        { name: "Intent Analysis Profile Generation", duration_ms: 0.9, status: "OK", type: "CONTROL_PLANE" },
        { name: "Semantic Vector Cache Lookup (Qdrant)", duration_ms: 4.8, status: "CACHE_HIT", type: "CACHE" },
        { name: "Instant Response Synthesis", duration_ms: 189.3, status: "OK", type: "FAST_PATH" },
      ],
    },
  ]);

  const activeTraceObj = traces.find((t) => t.id === selectedTrace) || traces[0];

  return (
    <AppShell
      title="Agentic Tracing & OpenTelemetry Spans"
      subtitle="Distributed execution graphs, multi-agent step lineage, and micro-latency profiling"
    >
      <div className="space-y-8">
        {/* Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="surface p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-[var(--text-secondary)] mb-2">
              <span className="text-sm font-medium">Trace Telemetry SLA</span>
              <Sparkles className="w-5 h-5 text-indigo-400" />
            </div>
            <div className="text-2xl font-bold text-[var(--text-primary)]">OTel v1.28</div>
            <div className="text-xs text-indigo-400 font-medium mt-1">OpenTelemetry Compliant Spans</div>
          </div>

          <div className="surface p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-[var(--text-secondary)] mb-2">
              <span className="text-sm font-medium">Active Agent Traces</span>
              <Layers className="w-5 h-5 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold text-[var(--text-primary)]">1,489 Today</div>
            <div className="text-xs text-cyan-400 font-medium mt-1">Multi-Step Action Profiling</div>
          </div>

          <div className="surface p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-[var(--text-secondary)] mb-2">
              <span className="text-sm font-medium">Average Span Latency</span>
              <Clock className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-[var(--text-primary)]">1.8 ms</div>
            <div className="text-xs text-emerald-400 font-medium mt-1">Control Plane Overhead</div>
          </div>

          <div className="surface p-5 backdrop-blur-md">
            <div className="flex items-center justify-between text-[var(--text-secondary)] mb-2">
              <span className="text-sm font-medium">Span Stream Target</span>
              <Activity className="w-5 h-5 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-[var(--text-primary)]">ClickHouse</div>
            <div className="text-xs text-amber-400 font-medium mt-1">OLAP Async Log Ingestion</div>
          </div>
        </div>

        {/* Distributed Trace Graph */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="surface p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Recent Agent Executions</h3>
            <div className="space-y-3">
              {traces.map((t) => (
                <div
                  key={t.id}
                  onClick={() => setSelectedTrace(t.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    selectedTrace === t.id
                      ? "bg-indigo-500/10 border-indigo-500/50"
                      : "bg-[var(--bg-surface-alt)] border-[var(--border-color)] hover:border-[var(--border-hover)]"
                  }`}
                >
                  <div className="flex items-center justify-between font-mono text-xs font-semibold text-indigo-400 mb-1">
                    <span>{t.id}</span>
                    <span className="text-[var(--text-muted)]">{t.timestamp}</span>
                  </div>
                  <div className="text-sm font-medium text-[var(--text-primary)]">{t.agent}</div>
                  <div className="flex items-center gap-4 text-xs text-[var(--text-secondary)] mt-2 font-mono">
                    <span>⏱️ {t.duration_ms} ms</span>
                    <span>🪙 {t.total_tokens} tokens</span>
                    <span>💵 ${t.cost_usd.toFixed(4)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="lg:col-span-2 surface p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)] flex items-center gap-2">
                  <GitCommit className="w-5 h-5 text-indigo-400" />
                  Span Execution DAG Graph: {activeTraceObj.id}
                </h3>
                <p className="text-sm text-[var(--text-secondary)] mt-1">{activeTraceObj.agent}</p>
              </div>
              <span className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 rounded-full text-xs font-semibold">
                COMPLETE (200 OK)
              </span>
            </div>

            <div className="space-y-4">
              {activeTraceObj.spans.map((span, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-[var(--bg-surface-alt)] border border-[var(--border-color)]">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono font-semibold text-indigo-400 flex items-center gap-1.5">
                      <ChevronRight className="w-4 h-4 text-[var(--text-muted)]" />
                      [{span.type}] {span.name}
                    </span>
                    <span className="text-xs font-mono text-emerald-500 font-semibold">{span.duration_ms} ms</span>
                  </div>

                  {/* Relative Timeline Bar */}
                  <div className="w-full bg-[var(--border-color)] h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-indigo-500 h-full rounded-full"
                      style={{
                        width: `${Math.max(5, (span.duration_ms / activeTraceObj.duration_ms) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
