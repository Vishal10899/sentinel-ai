"use client";

import { motion } from "framer-motion";
import { 
  AlertTriangle, 
  CheckCircle, 
  TrendingDown, 
  ShieldAlert, 
  ShieldCheck, 
  ServerCrash, 
  Zap, 
  ArrowRight,
  DollarSign,
  Lock,
  RefreshCw
} from "lucide-react";

export default function WhyCompaniesNeedSentinel() {
  const comparisons = [
    {
      id: "cost",
      problemTitle: "Uncontrolled AI Sprawl & Explosive API Bills",
      problemDesc: "Engineering teams spin up isolated LLM calls across OpenAI, Anthropic, and Bedrock. Duplicate queries burn thousands of dollars daily without caching or token compression.",
      solutionTitle: "Centralized Cost Control & 65% Token Savings",
      solutionDesc: "Sentinel automatically deduplicates semantic queries at the proxy layer, compresses prompt tokens, and enforces budget caps per team or API key.",
      stat: "65% Average Token Cost Reduction",
      badge: "FINANCIAL GOVERNANCE",
      icon: DollarSign,
      problemCode: "// Unoptimized Direct Call\nconst res = await openai.chat.completions.create({\n  model: 'gpt-4o',\n  messages: [{ role: 'user', content: fullUncachedPrompt }]\n}); // $0.063 per request!",
      solutionCode: "// Sentinel Optimized Proxy\nconst res = await sentinel.chat.completions.create({\n  model: 'gpt-4o',\n  messages: [{ role: 'user', content: fullPrompt }]\n}); // Cache HIT: $0.0001 (0.3ms)"
    },
    {
      id: "security",
      problemTitle: "Silent PII Data Leakage & Prompt Injection",
      problemDesc: "Employees and autonomous agents accidentally stream customer SSNs, credit cards, and confidential source code directly into public model training datasets.",
      solutionTitle: "Zero-Trust Payload Firewall & Real-Time Masking",
      solutionDesc: "Sentinel inspects 100% of payload bytes in < 2ms, masking sensitive parameters before transmission and quarantining prompt injection jailbreak vectors.",
      stat: "Zero Unsanitized Payloads Transmitted",
      badge: "ZERO-TRUST SECURITY",
      icon: Lock,
      problemCode: "// RAW PAYLOAD (Vulnerable)\n\"Analyze Q3 balance ledger for Client SSN 948-20-1984...\"\n// System Prompt Injection Detected: OVERRIDE SAFETY RULES!",
      solutionCode: "// SENTINEL SANITIZED PAYLOAD\n\"Analyze Q3 balance ledger for Client [REDACTED_SSN]...\"\n// Security Status: PASSED • Injection Vector Defended"
    },
    {
      id: "availability",
      problemTitle: "Single Provider Lock-In & Sudden Outages",
      problemDesc: "When a single AI model provider hits rate limits or suffers an outage, your customer-facing applications crash, causing business downtime.",
      solutionTitle: "Multi-Cloud Fallback & Sub-5ms Auto-Routing",
      solutionDesc: "Sentinel monitors provider health continuously. If OpenAI or Claude experiences latency spikes or HTTP 529 rate limits, Sentinel seamlessly reroutes traffic to alternative LLMs based on SLA rules.",
      stat: "99.999% Enterprise Gateway SLA",
      badge: "RESILIENT INFRASTRUCTURE",
      icon: RefreshCw,
      problemCode: "HTTP 529: Rate limit exceeded or Provider Outage\n--> Application Crash (500 Server Error)",
      solutionCode: "Sentinel Failover Triggered:\nPrimary: OpenAI GPT-4o (Degraded)\n--> Dynamic Route -> Anthropic Claude 3.5 Sonnet (200 OK)"
    }
  ];

  return (
    <section id="why-sentinel" className="py-28 bg-[#F8F7F2] text-slate-900 border-b border-slate-200/80 light-body-pattern">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Header */}
        <div className="text-center space-y-4 max-w-3xl mx-auto mb-24">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-slate-200/80 border border-slate-300 text-xs font-mono font-semibold text-slate-700 tracking-wider uppercase">
            WHY COMPANIES NEED SENTINEL
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-tight">
            The Shift From Fragile AI Scripting to Governed Control Plane.
          </h2>
          <p className="text-slate-600 text-base sm:text-lg leading-relaxed">
            See how enterprise leaders eliminate cost waste, security risk, and outage vulnerabilities.
          </p>
        </div>

        {/* Alternating Narrative Cards */}
        <div className="space-y-16">
          {comparisons.map((item, index) => {
            const Icon = item.icon;
            const isEven = index % 2 === 0;

            return (
              <div
                key={item.id}
                className="bg-white border border-slate-200/90 rounded-2xl p-8 sm:p-10 shadow-sm light-card-shadow overflow-hidden"
              >
                <div className="flex items-center gap-2 mb-6">
                  <span className="px-3 py-1 rounded-full text-xs font-mono font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                    {item.badge}
                  </span>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                  
                  {/* Left Column: Problem & Solution Story */}
                  <div className="lg:col-span-6 space-y-6">
                    
                    {/* Problem Box */}
                    <div className="p-4 rounded-xl bg-rose-50/60 border border-rose-200/80 space-y-2">
                      <div className="flex items-center gap-2 text-rose-700 font-bold text-sm">
                        <AlertTriangle className="w-4 h-4" />
                        <span>The Problem: {item.problemTitle}</span>
                      </div>
                      <p className="text-xs sm:text-sm text-slate-600 leading-relaxed font-normal">
                        {item.problemDesc}
                      </p>
                    </div>

                    {/* Solution Box */}
                    <div className="p-5 rounded-xl bg-slate-900 text-white space-y-3 shadow-md">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                          <CheckCircle className="w-4 h-4" />
                          <span>The Sentinel Solution: {item.solutionTitle}</span>
                        </div>
                        <Icon className="w-4 h-4 text-cyan-400" />
                      </div>
                      <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-normal">
                        {item.solutionDesc}
                      </p>
                      <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs font-mono">
                        <span className="text-slate-400">Impact Metric:</span>
                        <span className="text-amber-400 font-bold">{item.stat}</span>
                      </div>
                    </div>

                  </div>

                  {/* Right Column: Code & Structural Comparison Illustration */}
                  <div className="lg:col-span-6 space-y-3">
                    {/* Problem snippet */}
                    <div className="bg-slate-900 border border-rose-500/30 rounded-xl p-4 font-mono text-xs text-rose-300/90 space-y-1">
                      <div className="text-[10px] text-rose-400 uppercase font-bold tracking-wider pb-1 border-b border-rose-900/40 flex items-center justify-between">
                        <span>BEFORE (UNGOVERNED DIRECT CALL)</span>
                        <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                      </div>
                      <pre className="overflow-x-auto text-[11px] leading-relaxed pt-2">
                        {item.problemCode}
                      </pre>
                    </div>

                    {/* Solution snippet */}
                    <div className="bg-slate-900 border border-emerald-500/30 rounded-xl p-4 font-mono text-xs text-emerald-300 space-y-1">
                      <div className="text-[10px] text-emerald-400 uppercase font-bold tracking-wider pb-1 border-b border-emerald-900/40 flex items-center justify-between">
                        <span>AFTER SENTINEL CONTROL PLANE</span>
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                      </div>
                      <pre className="overflow-x-auto text-[11px] leading-relaxed pt-2">
                        {item.solutionCode}
                      </pre>
                    </div>
                  </div>

                </div>
              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
}
