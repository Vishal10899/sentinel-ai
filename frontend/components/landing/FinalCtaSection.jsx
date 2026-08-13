"use client";

import { useState } from "react";
import { 
  ArrowRight, 
  Terminal, 
  Copy, 
  Check, 
  ShieldCheck, 
  Sparkles 
} from "lucide-react";

export default function FinalCtaSection() {
  const [copied, setCopied] = useState(false);
  const command = "docker run -p 8080:8080 sentinel/gateway:latest";

  const handleCopy = () => {
    navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="py-28 bg-[#07111F] text-white relative overflow-hidden dark-hero-grid border-b border-slate-800">
      {/* Glow effect */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-blue-600/15 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center space-y-8">
        
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#0D1829] border border-blue-500/30 text-xs font-mono text-blue-300">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>ENTERPRISE-GRADE INFRASTRUCTURE</span>
        </div>

        <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-white leading-tight font-sans">
          Build Your Enterprise AI on Infrastructure <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-cyan-300 bg-clip-text text-transparent">You Control</span>.
        </h2>

        <p className="text-slate-300 text-base sm:text-lg max-w-2xl mx-auto font-normal leading-relaxed">
          Deploy the Sentinel AI control plane in under two minutes. Zero code refactoring required.
        </p>

        {/* Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <a
            href="/register"
            className="px-8 py-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm shadow-xl shadow-blue-600/30 hover:shadow-blue-500/50 transition-all duration-200 flex items-center gap-2 group"
          >
            <span>Start Free Trial</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </a>

          <a
            href="#pricing"
            className="px-8 py-4 rounded-xl bg-[#0D1829] hover:bg-slate-800 text-slate-200 font-medium text-sm border border-slate-700/80 hover:border-slate-600 transition-all duration-200"
          >
            Book Enterprise Demo
          </a>
        </div>

        {/* CLI Quick Start Box */}
        <div className="max-w-xl mx-auto pt-6">
          <div className="bg-[#0D1829]/90 border border-slate-700/80 rounded-xl p-4 flex items-center justify-between font-mono text-xs text-slate-300 shadow-2xl backdrop-blur-md">
            <div className="flex items-center gap-2.5 overflow-x-auto">
              <Terminal className="w-4 h-4 text-cyan-400 shrink-0" />
              <span className="text-slate-400">$</span>
              <span className="text-cyan-300 font-bold whitespace-nowrap">{command}</span>
            </div>
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors shrink-0"
              title="Copy Command"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>
        </div>

      </div>
    </section>
  );
}
