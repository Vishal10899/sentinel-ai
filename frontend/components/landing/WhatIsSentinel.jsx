"use client";

import { motion } from "framer-motion";
import { 
  ShieldCheck, 
  Cpu, 
  Layers, 
  Zap, 
  Lock, 
  ArrowRight, 
  Server, 
  Database,
  BarChart3,
  CheckCircle2
} from "lucide-react";

export default function WhatIsSentinel() {
  const pillars = [
    {
      step: "01",
      title: "Intercept & Inspect",
      subtitle: "Zero-Trust Payload Security",
      desc: "Every LLM request is intercepted in under 2ms. Sentinel scans for PII leaks, system prompt injections, secret keys, and compliance breaches before data ever leaves your network perimeter.",
      badge: "Real-time DLP",
      accent: "border-blue-500/30 text-blue-600 bg-blue-50",
      features: [
        "Automatic PII / PCI / HIPAA Masking",
        "Prompt Injection & Jailbreak Defense",
        "Secret & API Key Leakage Quarantine"
      ]
    },
    {
      step: "02",
      title: "Optimize & Route",
      subtitle: "Semantic Intelligence & Fallback",
      desc: "Sentinel checks semantic memory to serve cached responses instantly. Un-cached requests are compressed and dynamically routed to the cheapest, fastest model meeting your latency SLA.",
      badge: "Sub-ms Cache",
      accent: "border-cyan-500/30 text-cyan-600 bg-cyan-50",
      features: [
        "Semantic Query Deduplication",
        "SLA-Aware Dynamic Provider Fallback",
        "Prompt Compression (Up to 65% Savings)"
      ]
    },
    {
      step: "03",
      title: "Govern & Enforce",
      subtitle: "Unified Enterprise Governance",
      desc: "Eliminate shadow AI usage across departments. Set granular spend caps, virtual key rotation, team RBAC, and produce tamper-proof audit trails for regulatory compliance.",
      badge: "SOC2 Compliance",
      accent: "border-amber-500/30 text-amber-600 bg-amber-50",
      features: [
        "Virtual Key Lifecycle & Rate Limits",
        "Real-Time Cost Controls & Budget Caps",
        "Tamper-Proof Audit Traceability"
      ]
    }
  ];

  return (
    <section id="architecture" className="py-28 bg-[#FAFAF8] text-slate-900 border-b border-slate-200/80 light-body-pattern">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Header */}
        <div className="text-center space-y-4 max-w-3xl mx-auto mb-20">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-slate-200/60 border border-slate-300 text-xs font-mono font-semibold text-slate-700 tracking-wider uppercase">
            <Layers className="w-3.5 h-3.5 text-blue-600" />
            WHAT IS SENTINEL?
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-tight">
            The Missing Control Plane in Enterprise AI Architecture.
          </h2>
          <p className="text-slate-600 text-base sm:text-lg leading-relaxed">
            Sentinel is an intelligent AI control plane operating between your application layer and global LLM providers.
          </p>
        </div>

        {/* Clean Architectural Graphic Illustration */}
        <div className="mb-20 bg-white border border-slate-200/90 rounded-2xl p-8 sm:p-10 shadow-sm light-card-shadow">
          <div className="text-xs font-mono text-slate-600 uppercase font-semibold mb-6 text-center tracking-widest">
            ENTERPRISE ARCHITECTURAL TOPOLOGY
          </div>

          <div className="grid grid-cols-1 md:grid-cols-11 gap-4 items-center">
            
            {/* Box 1: Applications */}
            <div className="md:col-span-3 p-5 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-2">
              <div className="w-10 h-10 rounded-lg bg-blue-100 border border-blue-200 text-blue-600 flex items-center justify-center mx-auto">
                <Server className="w-5 h-5" />
              </div>
              <div className="font-semibold text-sm text-slate-900">Your Applications</div>
              <div className="text-xs text-slate-500 font-mono">
                Web Apps • Microservices • AI Agents • ERP & CRM
              </div>
            </div>

            {/* Connector 1 */}
            <div className="md:col-span-1 flex flex-col items-center justify-center text-slate-400 font-mono text-xs py-2">
              <div className="hidden md:block w-full h-0.5 bg-gradient-to-r from-slate-200 via-blue-400 to-slate-200 relative">
                <div className="absolute right-0 -top-1 w-2 h-2 border-t-2 border-r-2 border-blue-500 transform rotate-45" />
              </div>
              <span className="mt-1 text-[11px] font-semibold text-blue-600">Proxy Request</span>
            </div>

            {/* Box 2: Sentinel (The Core) */}
            <div className="md:col-span-3 p-6 rounded-xl bg-slate-900 text-white text-center space-y-3 shadow-xl relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-cyan-400 to-indigo-500" />
              <div className="w-10 h-10 rounded-lg bg-blue-600/30 border border-blue-400/40 text-cyan-300 flex items-center justify-center mx-auto">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div className="font-bold text-base tracking-wide text-white">Sentinel AI Control Plane</div>
              <div className="text-xs text-slate-300 font-mono space-y-1">
                <p>• Zero-Trust Inspection</p>
                <p>• Semantic Cache & Router</p>
                <p>• Unified Governance</p>
              </div>
            </div>

            {/* Connector 2 */}
            <div className="md:col-span-1 flex flex-col items-center justify-center text-slate-400 font-mono text-xs py-2">
              <div className="hidden md:block w-full h-0.5 bg-gradient-to-r from-slate-200 via-emerald-400 to-slate-200 relative">
                <div className="absolute right-0 -top-1 w-2 h-2 border-t-2 border-r-2 border-emerald-500 transform rotate-45" />
              </div>
              <span className="mt-1 text-[11px] font-semibold text-emerald-600">Routed Stream</span>
            </div>

            {/* Box 3: Providers */}
            <div className="md:col-span-3 p-5 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-2">
              <div className="w-10 h-10 rounded-lg bg-emerald-100 border border-emerald-200 text-emerald-600 flex items-center justify-center mx-auto">
                <Cpu className="w-5 h-5" />
              </div>
              <div className="font-semibold text-sm text-slate-900">AI LLM Providers</div>
              <div className="text-xs text-slate-500 font-mono">
                OpenAI • Anthropic • Bedrock • Azure AI • Local Ollama
              </div>
            </div>

          </div>
        </div>

        {/* Three Pillar Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {pillars.map((pillar) => (
            <div
              key={pillar.step}
              className="bg-white border border-slate-200 rounded-2xl p-7 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between group light-card-shadow"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-3xl font-bold font-mono text-slate-300 group-hover:text-blue-600 transition-colors">
                    {pillar.step}
                  </span>
                  <span className={`px-2.5 py-1 rounded-md text-xs font-mono font-semibold border ${pillar.accent}`}>
                    {pillar.badge}
                  </span>
                </div>

                <div>
                  <h3 className="text-xl font-bold text-slate-900 font-sans">{pillar.title}</h3>
                  <div className="text-xs font-mono font-semibold text-slate-600 uppercase tracking-wider mt-0.5">
                    {pillar.subtitle}
                  </div>
                </div>

                <p className="text-sm text-slate-600 leading-relaxed font-normal">
                  {pillar.desc}
                </p>

                <div className="pt-4 border-t border-slate-100 space-y-2">
                  {pillar.features.map((feat, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-xs text-slate-700 font-medium">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                      <span>{feat}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
