"use client";

import { 
  ShieldCheck, 
  Zap, 
  TrendingDown, 
  Activity, 
  Globe 
} from "lucide-react";

export default function EnterpriseResults() {
  const metrics = [
    {
      stat: "99.999%",
      label: "Gateway Uptime SLA",
      subtext: "Zero single-point-of-failure multi-region edge deployment",
      icon: ShieldCheck,
      color: "text-emerald-600 bg-emerald-50 border-emerald-200"
    },
    {
      stat: "< 2.4ms",
      label: "Proxy Latency Overhead",
      subtext: "Sub-millisecond Rust proxy payload inspection engine",
      icon: Zap,
      color: "text-cyan-600 bg-cyan-50 border-cyan-200"
    },
    {
      stat: "68%",
      label: "Average Cost Reduction",
      subtext: "Achieved via semantic deduplication and prompt compression",
      icon: TrendingDown,
      color: "text-amber-600 bg-amber-50 border-amber-200"
    },
    {
      stat: "12B+",
      label: "Tokens Governed Daily",
      subtext: "Processed across enterprise engineering teams globally",
      icon: Globe,
      color: "text-blue-600 bg-blue-50 border-blue-200"
    }
  ];

  return (
    <section className="py-28 bg-[#F8F7F2] text-slate-900 border-b border-slate-200/80 light-body-pattern">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center space-y-4 max-w-3xl mx-auto mb-20">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-slate-200/80 border border-slate-300 text-xs font-mono font-semibold text-slate-700 tracking-wider uppercase">
            ENTERPRISE BENCHMARKS
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-tight">
            Proven Performance at Scale.
          </h2>
          <p className="text-slate-600 text-base sm:text-lg leading-relaxed">
            Enterprise infrastructure built to guarantee high throughput, strict security, and massive cost savings.
          </p>
        </div>

        {/* 4 Metric Highlights */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {metrics.map((m, idx) => {
            const Icon = m.icon;
            return (
              <div
                key={idx}
                className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm light-card-shadow space-y-4 text-center group hover:-translate-y-1 transition-all duration-200"
              >
                <div className={`w-12 h-12 rounded-xl border ${m.color} flex items-center justify-center mx-auto shadow-sm`}>
                  <Icon className="w-6 h-6" />
                </div>

                <div className="text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900 font-mono">
                  {m.stat}
                </div>

                <div className="space-y-1">
                  <div className="font-bold text-base text-slate-900 font-sans">{m.label}</div>
                  <p className="text-xs text-slate-500 leading-relaxed">{m.subtext}</p>
                </div>
              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
}
