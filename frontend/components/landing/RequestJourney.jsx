"use client";

import { useState } from "react";
import { 
  ArrowRight, 
  ShieldCheck, 
  Cpu, 
  Zap, 
  Lock, 
  CheckCircle2, 
  Terminal, 
  Database,
  Activity,
  ChevronRight
} from "lucide-react";

export default function RequestJourney() {
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    {
      stepNum: "01",
      name: "Application Ingestion",
      latency: "0.4ms",
      desc: "Your microservice or AI agent fires an HTTP POST request to Sentinel's low-latency proxy endpoint instead of directly hitting LLM vendor APIs.",
      techDetail: "HTTP/2 & gRPC Proxy Layer • TLS 1.3 Encryption",
      dataView: {
        endpoint: "POST https://api.sentinel.ai/v1/chat/completions",
        headers: { "Authorization": "Bearer snt_key_live_98412", "X-Sentinel-App": "core-banking-v2" },
        body: '{"model": "auto", "messages": [{"role": "user", "content": "Analyze account ACCT-981..."}]}'
      }
    },
    {
      stepNum: "02",
      name: "Zero-Trust Security Scan",
      latency: "1.2ms",
      desc: "Sentinel's inline security engine inspects payload bytes. It redacts PII/PCI data in real-time and scans for system prompt injection jailbreak patterns.",
      techDetail: "Regex DLP Matcher • Injection Classifier Engine",
      dataView: {
        piiStatus: "SSN & Financial ACCT Masked",
        jailbreakCheck: "Passed (Safety Score: 0.99)",
        sanitizedBody: '{"model": "auto", "messages": [{"role": "user", "content": "Analyze account [REDACTED]..."}]}'
      }
    },
    {
      stepNum: "03",
      name: "Semantic Cache Lookup",
      latency: "0.3ms",
      desc: "Sentinel performs vector embedding similarity matching against enterprise semantic cache. If a matching query exists, response is returned instantly without calling providers.",
      techDetail: "Vector Similarity Engine • Sub-millisecond Memory Cache",
      dataView: {
        cacheQuery: "Vector Cosine Similarity: 0.98",
        result: "CACHE MISS (Proceeding to SLA Router)",
        savedCost: "$0.00 (Fresh Execution)"
      }
    },
    {
      stepNum: "04",
      name: "SLA & Cost Decision Engine",
      latency: "0.8ms",
      desc: "The decision intelligence engine evaluates live model health, latency metrics, and token costs across OpenAI, Anthropic, Bedrock, and Azure to pick the optimal destination.",
      techDetail: "Dynamic SLA Router • Multi-Cloud Health Monitor",
      dataView: {
        evaluatedProviders: ["OpenAI (Latency 320ms)", "Anthropic (Latency 110ms)"],
        selectedTarget: "Anthropic Claude 3.5 Sonnet",
        costEfficiencyRatio: "+42% Savings vs Default"
      }
    },
    {
      stepNum: "05",
      name: "Encrypted Stream & Audit Hash",
      latency: " streaming",
      desc: "Response tokens stream back to your app with zero additional buffer latency. An immutable cryptographic trace hash is logged into your enterprise audit vault.",
      techDetail: "Server-Sent Events (SSE) Stream • SHA-256 Audit Fingerprint",
      dataView: {
        status: "200 OK (Streamed 420 Tokens)",
        totalOverhead: "2.7ms total proxy overhead",
        auditTraceId: "trace_snt_98401a82f9104c"
      }
    }
  ];

  const current = steps[activeStep];

  return (
    <section id="request-journey" className="py-28 bg-[#F8F7F2] text-slate-900 border-b border-slate-200/80 light-body-pattern">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center space-y-4 max-w-3xl mx-auto mb-20">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-slate-200/80 border border-slate-300 text-xs font-mono font-semibold text-slate-700 tracking-wider uppercase">
            THE REQUEST LIFECYCLE
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-tight">
            How One AI Request Travels Through Sentinel.
          </h2>
          <p className="text-slate-600 text-base sm:text-lg leading-relaxed">
            Follow a payload step-by-step from initial app request to sanitized, cost-optimized response stream in under 15ms total.
          </p>
        </div>

        {/* Step Indicator Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-12">
          {steps.map((s, idx) => {
            const isActive = activeStep === idx;
            return (
              <button
                key={s.stepNum}
                onClick={() => setActiveStep(idx)}
                className={`p-4 rounded-xl text-left border transition-all duration-200 ${
                  isActive
                    ? "bg-slate-900 text-white border-slate-900 shadow-lg"
                    : "bg-white text-slate-700 border-slate-200 hover:border-slate-300"
                }`}
              >
                <div className="flex items-center justify-between text-xs font-mono mb-1">
                  <span className={isActive ? "text-cyan-400 font-bold" : "text-slate-400"}>STEP {s.stepNum}</span>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] ${isActive ? "bg-cyan-500/20 text-cyan-300" : "bg-slate-100 text-slate-500"}`}>
                    {s.latency}
                  </span>
                </div>
                <div className="text-xs font-bold font-sans line-clamp-1">{s.name}</div>
              </button>
            );
          })}
        </div>

        {/* Active Step Visualizer Box */}
        <div className="bg-white border border-slate-200 rounded-2xl p-8 sm:p-12 shadow-sm light-card-shadow">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            
            {/* Step Explanation */}
            <div className="lg:col-span-6 space-y-6">
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <span className="text-4xl font-bold font-mono text-blue-600">{current.stepNum}</span>
                  <span className="px-3 py-1 rounded-full text-xs font-mono font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    LATENCY: {current.latency}
                  </span>
                </div>
                <h3 className="text-2xl sm:text-3xl font-bold text-slate-900 font-sans">
                  {current.name}
                </h3>
              </div>

              <p className="text-base text-slate-600 leading-relaxed">
                {current.desc}
              </p>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs font-mono text-slate-700 space-y-1">
                <span className="text-slate-400 block text-[10px] uppercase tracking-wider font-semibold">ENGINE PROTOCOL</span>
                <span className="font-semibold text-slate-900">{current.techDetail}</span>
              </div>

              {/* Navigation controls */}
              <div className="flex items-center gap-4 pt-2">
                <button
                  disabled={activeStep === 0}
                  onClick={() => setActiveStep(prev => Math.max(0, prev - 1))}
                  className="px-4 py-2 text-xs font-semibold rounded-lg border border-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50"
                >
                  Previous Step
                </button>
                <button
                  disabled={activeStep === steps.length - 1}
                  onClick={() => setActiveStep(prev => Math.min(steps.length - 1, prev + 1))}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-blue-500 shadow-md flex items-center gap-1"
                >
                  Next Step
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Code / Data Inspection Box */}
            <div className="lg:col-span-6">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 font-mono text-xs text-slate-200 space-y-4 shadow-xl">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-cyan-400" />
                    <span className="font-bold text-slate-100">PAYLOAD INSPECTOR LOG</span>
                  </div>
                  <span className="text-[10px] text-slate-400">STEP {current.stepNum} OF 05</span>
                </div>

                <pre className="text-[11px] text-cyan-300 leading-relaxed overflow-x-auto p-3 rounded bg-slate-950 border border-slate-850">
                  {JSON.stringify(current.dataView, null, 2)}
                </pre>

                <div className="flex items-center justify-between pt-2 text-[10px] text-slate-400">
                  <span className="flex items-center gap-1 text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Pipeline Verified
                  </span>
                  <span>Encryption: TLS 1.3 AES-256</span>
                </div>
              </div>
            </div>

          </div>
        </div>

      </div>
    </section>
  );
}
