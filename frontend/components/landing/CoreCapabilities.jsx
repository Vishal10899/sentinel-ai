"use client";

import { useState } from "react";
import { 
  ShieldCheck, 
  Cpu, 
  DollarSign, 
  BarChart3, 
  Code2, 
  Check, 
  ArrowRight,
  Lock,
  Activity,
  Zap,
  SlidersHorizontal,
  Terminal,
  Database
} from "lucide-react";

export default function CoreCapabilities() {
  const [activeTab, setActiveTab] = useState("security");

  const capabilities = [
    {
      id: "security",
      title: "Security & Compliance",
      tagline: "Zero-Trust Payload Inspection & Data Leakage Prevention",
      icon: ShieldCheck,
      badge: "Real-time Firewall",
      points: [
        "In-line PII, PCI, HIPAA, and SSN detection & automatic regex masking",
        "Prompt Injection & System Jailbreak Quarantine Engine",
        "API Key & Environment Secret Leakage Prevention",
        "SOC2 Type II & ISO 27001 Cryptographic Audit Trails"
      ],
      illustration: (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 font-mono text-xs text-slate-200 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-blue-400 font-bold flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-blue-400" /> SENTINEL SECURITY ENGINE
            </span>
            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px]">INSPECTION PASSED</span>
          </div>

          <div className="space-y-2">
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 space-y-1">
              <div className="text-[10px] text-slate-400">INBOUND PAYLOAD (STREAMED)</div>
              <div className="text-slate-300 text-[11px]">"Customer ACCT-9841 with SSN 948-20-1984 requests payout..."</div>
            </div>

            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 space-y-1">
              <div className="text-[10px] text-emerald-400">SANITIZED PAYLOAD (TRANSMITTED)</div>
              <div className="text-emerald-300 text-[11px]">"Customer [REDACTED_ACCT] with SSN [REDACTED_SSN] requests payout..."</div>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800 flex justify-between text-[10px] text-slate-400">
            <span>PII Types Masked: 2</span>
            <span>Scan Overhead: 1.2ms</span>
          </div>
        </div>
      )
    },
    {
      id: "decision",
      title: "Decision Intelligence",
      tagline: "Dynamic Latency-Optimal Routing & Intent Detection",
      icon: Cpu,
      badge: "Smart Fallback",
      points: [
        "SLA-aware model selection matching prompt intent to cheapest capable model",
        "Automatic zero-downtime failover across OpenAI, Anthropic, Bedrock, and Azure",
        "Real-time health monitoring of global provider status and latency spikes",
        "Custom rule engine for regulatory data residency boundaries"
      ],
      illustration: (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 font-mono text-xs text-slate-200 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-cyan-400 font-bold flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" /> DECISION ROUTER ENGINE
            </span>
            <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 text-[10px]">ROUTE OPTIMAL</span>
          </div>

          <div className="space-y-2">
            <div className="p-2 rounded bg-slate-950 border border-slate-800 flex justify-between items-center text-[11px]">
              <span className="text-slate-400">Target 1: OpenAI GPT-4o</span>
              <span className="text-amber-400">Spike Detected (480ms)</span>
            </div>
            <div className="p-2 rounded bg-indigo-950/60 border border-indigo-500/30 flex justify-between items-center text-[11px]">
              <span className="text-cyan-300 font-bold">Rerouted: DeepSeek R1 / V3</span>
              <span className="text-emerald-400 font-bold">Optimal (98ms / $0.002)</span>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800 flex justify-between text-[10px] text-slate-400">
            <span>Intent: Mathematical Audit</span>
            <span>Fallback Latency: &lt; 2ms</span>
          </div>
        </div>
      )
    },
    {
      id: "cost",
      title: "Cost Optimization",
      tagline: "Semantic Caching & Token Compression Engine",
      icon: DollarSign,
      badge: "65% Savings",
      points: [
        "Sub-millisecond semantic similarity search serving pre-computed responses",
        "Algorithmic prompt token compression cutting redundant context waste",
        "Hard spending caps and budget enforcement per team, key, or project",
        "Real-time cost projection and token burn anomaly alerts"
      ],
      illustration: (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 font-mono text-xs text-slate-200 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-amber-400 font-bold flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-amber-400" /> SEMANTIC CACHE ENGINE
            </span>
            <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px]">CACHE HIT (99.4%)</span>
          </div>

          <div className="space-y-2">
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 flex items-center justify-between text-[11px]">
              <div>
                <span className="text-slate-400 block text-[10px]">ORIGINAL TOKENS</span>
                <span className="text-rose-400 line-through">4,210 tokens ($0.063)</span>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-600" />
              <div className="text-right">
                <span className="text-slate-400 block text-[10px]">SENTINEL CACHED</span>
                <span className="text-emerald-400 font-bold">0 tokens ($0.000)</span>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800 flex justify-between text-[10px] text-slate-400">
            <span>Cache Response: 0.3ms</span>
            <span>Saved: $0.063 / req</span>
          </div>
        </div>
      )
    },
    {
      id: "observability",
      title: "Real-Time Observability",
      tagline: "End-to-End Traces, Token Economics & Latency Heatmaps",
      icon: BarChart3,
      badge: "Full Audit",
      points: [
        "Distributed tracing for multi-step agent loops and recursive chains",
        "Granular latency breakdowns (Ingestion, Proxy, Provider TTL, Streaming)",
        "Token usage heatmaps categorized by application, user ID, and prompt type",
        "OpenTelemetry export to Datadog, Prometheus, Splunk, and Grafana"
      ],
      illustration: (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 font-mono text-xs text-slate-200 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-indigo-400 font-bold flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-indigo-400" /> DISTRIBUTED TRACER
            </span>
            <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 text-[10px]">TRACE ID: snt_98a4</span>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[10px] p-1.5 rounded bg-slate-950">
              <span className="text-slate-300">1. Client Ingest</span>
              <span className="text-slate-400">0.4ms</span>
            </div>
            <div className="flex items-center justify-between text-[10px] p-1.5 rounded bg-slate-950">
              <span className="text-blue-400">2. Security Scan & DLP</span>
              <span className="text-blue-300 font-bold">1.2ms</span>
            </div>
            <div className="flex items-center justify-between text-[10px] p-1.5 rounded bg-slate-950">
              <span className="text-emerald-400">3. Provider Streaming</span>
              <span className="text-emerald-300 font-bold">12.4ms</span>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800 flex justify-between text-[10px] text-slate-400">
            <span>Total E2E Latency: 14.0ms</span>
            <span>OpenTelemetry: Active</span>
          </div>
        </div>
      )
    },
    {
      id: "dx",
      title: "Developer Experience",
      tagline: "1-Line Drop-in Proxy SDK • Zero Application Rewrite",
      icon: Code2,
      badge: "Zero Rewrite",
      points: [
        "Swap base URL to Sentinel endpoint; works natively with standard OpenAI / Anthropic SDKs",
        "Official SDKs for Python, TypeScript/Node.js, Go, Java, and Rust",
        "Local Docker CLI emulator for instant developer staging",
        "Declarative policy configuration via YAML / Terraform infrastructure-as-code"
      ],
      illustration: (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 font-mono text-xs text-slate-200 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-emerald-400 font-bold flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-emerald-400" /> 1-LINE SDK INTEGRATION
            </span>
            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px]">READY</span>
          </div>

          <pre className="p-3 rounded bg-slate-950 text-slate-300 text-[11px] leading-relaxed overflow-x-auto">
{`import OpenAI from 'openai';

// Simply change baseURL to Sentinel Control Plane
const openai = new OpenAI({
  apiKey: process.env.SENTINEL_VIRTUAL_KEY,
  baseURL: "https://api.sentinel.ai/v1"
});`}
          </pre>

          <div className="pt-2 border-t border-slate-800 flex justify-between text-[10px] text-slate-400">
            <span>SDK Compatibility: 100% Native</span>
            <span>Setup Time: &lt; 2 mins</span>
          </div>
        </div>
      )
    }
  ];

  const currentCap = capabilities.find(c => c.id === activeTab) || capabilities[0];

  return (
    <section id="capabilities" className="py-28 bg-[#FAFAF8] text-slate-900 border-b border-slate-200/80 light-body-pattern">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center space-y-4 max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-slate-200/80 border border-slate-300 text-xs font-mono font-semibold text-slate-700 tracking-wider uppercase">
            CORE CAPABILITIES
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-tight">
            Engineered for Industrial-Scale Enterprise AI.
          </h2>
          <p className="text-slate-600 text-base sm:text-lg leading-relaxed">
            Five core pillars powering mission-critical artificial intelligence control planes.
          </p>
        </div>

        {/* Tab Selector */}
        <div className="flex flex-wrap items-center justify-center gap-2 mb-12">
          {capabilities.map((cap) => {
            const Icon = cap.icon;
            const isActive = activeTab === cap.id;
            return (
              <button
                key={cap.id}
                onClick={() => setActiveTab(cap.id)}
                className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 flex items-center gap-2 border ${
                  isActive
                    ? "bg-slate-900 text-white border-slate-900 shadow-md"
                    : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-cyan-400" : "text-slate-500"}`} />
                <span>{cap.title}</span>
              </button>
            );
          })}
        </div>

        {/* Detailed Capability Panel */}
        <div className="bg-white border border-slate-200 rounded-2xl p-8 sm:p-12 shadow-sm light-card-shadow">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            
            {/* Left: Text Description & Bullets */}
            <div className="lg:col-span-7 space-y-6">
              <div className="space-y-2">
                <span className="px-3 py-1 rounded-full text-xs font-mono font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                  {currentCap.badge}
                </span>
                <h3 className="text-2xl sm:text-3xl font-bold text-slate-900 font-sans">
                  {currentCap.title}
                </h3>
                <p className="text-sm sm:text-base text-slate-600 font-medium">
                  {currentCap.tagline}
                </p>
              </div>

              <div className="space-y-3 pt-2">
                {currentCap.points.map((pt, idx) => (
                  <div key={idx} className="flex items-start gap-3 text-sm text-slate-700">
                    <div className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center shrink-0 mt-0.5">
                      <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                    </div>
                    <span>{pt}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Custom Interactive Capability Illustration */}
            <div className="lg:col-span-5">
              {currentCap.illustration}
            </div>

          </div>
        </div>

      </div>
    </section>
  );
}
