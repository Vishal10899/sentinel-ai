"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { 
  ShieldCheck, 
  ArrowRight, 
  Sparkles, 
  Zap, 
  Lock, 
  Cpu, 
  Check, 
  ShieldAlert, 
  Layers, 
  Server, 
  Globe, 
  Activity, 
  ChevronRight,
  Database,
  SlidersHorizontal,
  Flame
} from "lucide-react";

export default function HeroSection() {
  const [selectedApp, setSelectedApp] = useState("fintech");

  const appPayloads = {
    fintech: {
      title: "Core Banking LLM Query",
      app: "FinTech App",
      input: "Execute wire transfer for Account #9841-2091 with SSN 948-20-1984.",
      pii: "SSN & Financial ACCT Detected",
      sanitized: "Execute wire transfer for Account [REDACTED_ACCT] with SSN [REDACTED_SSN].",
      cacheStatus: "HIT (Sub-ms)",
      routedTo: "DeepSeek R1 / V3",
      savings: "96.4%",
      latency: "1.8ms"
    },
    crm: {
      title: "Salesforce AI Agent Request",
      app: "Enterprise CRM",
      input: "Draft Q4 renewal email for CEO (john@acme.com) with contract terms.",
      pii: "Executive Email & Internal PII Masked",
      sanitized: "Draft Q4 renewal email for CEO [REDACTED_EMAIL] with contract terms.",
      cacheStatus: "BYPASS (Fresh Prompt)",
      routedTo: "Anthropic Claude 3.5 Sonnet",
      savings: "54.2%",
      latency: "2.1ms"
    },
    agent: {
      title: "Autonomous Code Refactor Mesh",
      app: "DevOps Agent",
      input: "Scan repo for AWS_SECRET_KEY=AKIAIOSFODNN7REALKEY and patch.",
      pii: "API Key Leak Blocked & Quarantined",
      sanitized: "Scan repo for AWS_SECRET_KEY=[QUARANTINED_SECRET] and patch.",
      cacheStatus: "HIT (Semantic Cache)",
      routedTo: "Azure OpenAI GPT-4o",
      savings: "88.7%",
      latency: "1.4ms"
    }
  };

  const activePayload = appPayloads[selectedApp];

  return (
    <section className="relative min-h-screen pt-32 pb-24 bg-[#07111F] text-slate-100 overflow-hidden dark-hero-grid border-b border-slate-800/60">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-blue-600/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute top-1/3 left-1/4 w-[400px] h-[400px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-1/2 right-1/4 w-[350px] h-[350px] bg-indigo-600/10 rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          
          {/* Left Column: Storytelling & Hero Copy */}
          <div className="lg:col-span-6 space-y-8">
            
            {/* Enterprise Badge */}
            <motion.div 
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#0D1829] border border-blue-500/30 text-xs font-mono tracking-wide text-blue-300 shadow-xl"
            >
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping shrink-0" />
              <span className="font-semibold text-slate-200">ENTERPRISE AI CONTROL PLANE v2.4</span>
              <span className="text-slate-500">•</span>
              <span className="text-amber-400 font-medium flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-amber-400" /> SOC2 TYPE II
              </span>
            </motion.div>

            {/* Headline */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="space-y-4"
            >
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-white leading-[1.08] font-sans">
                The Intelligent Control Plane for <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-cyan-300 bg-clip-text text-transparent">Enterprise AI</span> Infrastructure.
              </h1>
            </motion.div>

            {/* Single Paragraph */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-base sm:text-lg text-slate-300 leading-relaxed max-w-xl font-normal"
            >
              Sentinel sits between enterprise applications and AI providers to inspect payload security, optimize token costs, enforce governance, and route requests dynamically.
            </motion.p>

            {/* CTAs */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="flex flex-wrap items-center gap-4 pt-2"
            >
              <a
                href="/register"
                className="px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm shadow-xl shadow-blue-600/30 hover:shadow-blue-500/50 transition-all duration-200 flex items-center gap-2 group"
              >
                Start Free Trial
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </a>

              <a
                href="#pricing"
                className="px-6 py-3.5 rounded-xl bg-[#0D1829] hover:bg-slate-800 text-slate-200 font-medium text-sm border border-slate-700/80 hover:border-slate-600 transition-all duration-200 flex items-center gap-2"
              >
                Book Enterprise Demo
              </a>
            </motion.div>

            {/* Trust Metrics & Sector Badges */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="pt-6 border-t border-slate-800/80 space-y-3"
            >
              <div className="text-xs font-mono text-slate-400 tracking-wider uppercase flex items-center gap-2">
                <span>Governing 10B+ Daily Tokens Across Global Leaders</span>
              </div>
              <div className="flex flex-wrap items-center gap-x-8 gap-y-3 opacity-70 grayscale hover:grayscale-0 transition-all duration-300">
                <span className="text-sm font-semibold tracking-wider text-slate-300 font-mono">FINTECH CORE</span>
                <span className="text-sm font-semibold tracking-wider text-slate-300 font-mono">HEALTHCARE AI</span>
                <span className="text-sm font-semibold tracking-wider text-slate-300 font-mono">SAAS MESH</span>
                <span className="text-sm font-semibold tracking-wider text-slate-300 font-mono">GLOBAL 2000</span>
              </div>
            </motion.div>

          </div>

          {/* Right Column: Custom Living Visualization (App -> Sentinel -> Providers) */}
          <div className="lg:col-span-6 relative">
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="bg-[#0D1829]/90 border border-slate-700/70 rounded-2xl p-6 shadow-2xl relative overflow-hidden backdrop-blur-xl"
            >
              {/* Top Bar / Header of Visualization */}
              <div className="flex items-center justify-between pb-4 mb-5 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs font-mono text-slate-300 font-semibold uppercase tracking-wider">
                    LIVE CONTROL PLANE PIPELINE
                  </span>
                </div>
                <div className="flex items-center gap-1.5 bg-slate-900/80 p-1 rounded-lg border border-slate-800">
                  {Object.keys(appPayloads).map((key) => (
                    <button
                      key={key}
                      onClick={() => setSelectedApp(key)}
                      className={`px-2.5 py-1 text-[11px] font-mono rounded-md transition-all ${
                        selectedApp === key 
                          ? "bg-blue-600 text-white font-semibold shadow-md" 
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      {key.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              {/* FLOW DIAGRAM SVG & INTERACTIVE NODES */}
              <div className="relative space-y-6">
                
                {/* 1. APPLICATIONS LAYER */}
                <div className="flex items-center justify-between p-3.5 bg-slate-900/90 border border-slate-800 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center">
                      <Server className="w-4 h-4 text-blue-400" />
                    </div>
                    <div>
                      <div className="text-xs font-mono text-blue-400 font-semibold">{activePayload.app}</div>
                      <div className="text-[11px] text-slate-300 font-mono line-clamp-1 max-w-[280px]">
                        "{activePayload.input}"
                      </div>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20">
                    POST /v1/chat
                  </span>
                </div>

                {/* FLOW CONNECTOR 1 */}
                <div className="flex justify-center relative py-1">
                  <div className="w-0.5 h-6 bg-gradient-to-b from-blue-500 to-indigo-500" />
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 px-2 py-0.5 rounded-full bg-[#07111F] border border-blue-500/40 text-[10px] font-mono text-cyan-400">
                    &lt; 1.8ms INGESTION
                  </div>
                </div>

                {/* 2. SENTINEL CONTROL PLANE (CENTER ENGINE) */}
                <div className="p-4 bg-gradient-to-b from-indigo-950/40 to-slate-900/90 border border-indigo-500/40 rounded-xl shadow-lg relative overflow-hidden group">
                  <div className="absolute top-0 right-0 px-3 py-1 bg-indigo-500/20 border-b border-l border-indigo-500/30 rounded-bl-xl text-[10px] font-mono text-indigo-300 font-bold">
                    SENTINEL CORE PROXY
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-cyan-400" />
                      <span className="text-xs font-semibold text-white tracking-wide">Inspection & Sanitization</span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                      <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                        <span className="text-slate-400 block text-[10px]">Zero-Trust DLP</span>
                        <span className="text-emerald-400 font-medium">{activePayload.pii}</span>
                      </div>
                      <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                        <span className="text-slate-400 block text-[10px]">Semantic Cache</span>
                        <span className="text-amber-400 font-medium">{activePayload.cacheStatus}</span>
                      </div>
                    </div>

                    <div className="p-2 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-300 flex items-center justify-between">
                      <span className="text-slate-400">Payload Masked:</span>
                      <span className="text-cyan-300 text-right truncate max-w-[240px]">{activePayload.sanitized}</span>
                    </div>
                  </div>
                </div>

                {/* FLOW CONNECTOR 2 */}
                <div className="flex justify-center relative py-1">
                  <div className="w-0.5 h-6 bg-gradient-to-b from-indigo-500 to-cyan-500" />
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 px-2 py-0.5 rounded-full bg-[#07111F] border border-cyan-500/40 text-[10px] font-mono text-emerald-400">
                    SLA DYNAMIC ROUTE
                  </div>
                </div>

                {/* 3. AI PROVIDERS TARGET */}
                <div className="flex items-center justify-between p-3.5 bg-slate-900/90 border border-slate-800 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
                      <Cpu className="w-4 h-4 text-emerald-400" />
                    </div>
                    <div>
                      <div className="text-xs font-mono text-emerald-400 font-semibold">Destination Provider</div>
                      <div className="text-xs text-white font-medium">{activePayload.routedTo}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[10px] font-mono text-slate-400">Cost Savings</div>
                    <div className="text-xs font-mono font-bold text-amber-400">{activePayload.savings}</div>
                  </div>
                </div>

              </div>

              {/* Bottom Metrics Bar */}
              <div className="mt-5 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs font-mono text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5 text-amber-400" /> Proxy Overhead: <strong className="text-white">{activePayload.latency}</strong>
                </span>
                <span className="flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5 text-cyan-400" /> Audit Hash: <strong className="text-slate-300">0x98f...a41</strong>
                </span>
              </div>

            </motion.div>
          </div>

        </div>
      </div>
    </section>
  );
}
