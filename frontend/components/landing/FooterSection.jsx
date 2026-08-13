"use client";

import Link from "next/link";
import { Shield, Sparkles, CheckCircle2, Lock } from "lucide-react";

export default function FooterSection() {
  const columns = [
    {
      title: "Product",
      links: [
        { label: "Zero-Trust Proxy", href: "#architecture" },
        { label: "Intelligent Routing", href: "#architecture" },
        { label: "Semantic Cache", href: "#architecture" },
        { label: "Cost Guardrails", href: "#capabilities" },
        { label: "Observability", href: "#capabilities" },
        { label: "Changelog & Releases", href: "#" }
      ]
    },
    {
      title: "Solutions",
      links: [
        { label: "Financial Compliance", href: "#why-sentinel" },
        { label: "Healthcare Data Safety", href: "#why-sentinel" },
        { label: "High-Volume SaaS", href: "#why-sentinel" },
        { label: "Multi-Cloud Fallback", href: "#why-sentinel" },
        { label: "Shadow AI Governance", href: "#why-sentinel" }
      ]
    },
    {
      title: "Developers",
      links: [
        { label: "Documentation", href: "#request-journey" },
        { label: "Python SDK", href: "#request-journey" },
        { label: "TypeScript / Node SDK", href: "#request-journey" },
        { label: "Go & Java SDKs", href: "#request-journey" },
        { label: "REST & gRPC API", href: "#request-journey" },
        { label: "GitHub Repository", href: "https://github.com" }
      ]
    },
    {
      title: "Enterprise",
      links: [
        { label: "VPC Deployment", href: "#pricing" },
        { label: "Air-Gapped Gateway", href: "#pricing" },
        { label: "Custom SLA (99.999%)", href: "#pricing" },
        { label: "SOC2 Type II Report", href: "#pricing" },
        { label: "HIPAA BAA Request", href: "#pricing" },
        { label: "Book Demo", href: "#pricing" }
      ]
    },
    {
      title: "Company",
      links: [
        { label: "About Sentinel", href: "#testimonials" },
        { label: "Security & Trust", href: "#architecture" },
        { label: "Careers", href: "#" },
        { label: "Press Kit", href: "#" },
        { label: "Contact Sales", href: "#pricing" },
        { label: "Privacy Policy", href: "#" }
      ]
    }
  ];

  return (
    <footer className="bg-[#050B14] text-slate-400 text-xs border-t border-slate-800/80 pt-16 pb-12 font-sans">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        
        {/* Top Footer Section: 5 Columns */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
          {columns.map((col, idx) => (
            <div key={idx} className="space-y-3">
              <div className="font-mono font-bold uppercase tracking-wider text-slate-200 text-[11px]">
                {col.title}
              </div>
              <ul className="space-y-2">
                {col.links.map((link, lIdx) => (
                  <li key={lIdx}>
                    <a
                      href={link.href}
                      className="hover:text-white transition-colors"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Middle Footer: Brand & Badges */}
        <div className="pt-8 border-t border-slate-800/80 flex flex-col md:flex-row items-center justify-between gap-6">
          
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
              <Shield className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <span className="text-white font-bold text-sm tracking-tight">Sentinel AI</span>
              <p className="text-[11px] text-slate-500">The Enterprise AI Control Plane & Reverse Proxy</p>
            </div>
          </div>

          {/* Status & Compliance Badges */}
          <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono">
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>All Systems Operational</span>
            </div>

            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300">
              <Lock className="w-3 h-3 text-cyan-400" />
              <span>SOC2 TYPE II CERTIFIED</span>
            </div>

            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300">
              <CheckCircle2 className="w-3 h-3 text-amber-400" />
              <span>ISO 27001 READY</span>
            </div>
          </div>

        </div>

        {/* Bottom Copyright */}
        <div className="pt-6 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-500 gap-4">
          <p>© {new Date().getFullYear()} Sentinel AI Technologies Inc. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <a href="#" className="hover:text-slate-300 transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-slate-300 transition-colors">Terms of Service</a>
            <a href="#" className="hover:text-slate-300 transition-colors">Security Disclosure</a>
          </div>
        </div>

      </div>
    </footer>
  );
}
