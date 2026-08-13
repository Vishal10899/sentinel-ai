"use client";

import { 
  Building2, 
  ShieldCheck, 
  Quote, 
  CheckCircle2 
} from "lucide-react";

export default function TestimonialsSection() {
  const testimonials = [
    {
      quote: "Sentinel transformed our LLM operational strategy. We reduced token spend by 72% in the first 30 days while gaining complete audit control over sensitive financial data streams.",
      author: "Marcus Vance",
      role: "VP of Cloud Architecture",
      company: "Global FinTech Holdings",
      badge: "FINANCIAL SERVICES",
      impact: "$1.4M Annualized Savings"
    },
    {
      quote: "Before Sentinel, prompt injection attacks and unmasked PII were our biggest compliance nightmares. Now, every single payload is automatically sanitized inline before leaving our VPC.",
      author: "Elena Rostova",
      role: "Chief Information Security Officer",
      company: "Aether Health Network",
      badge: "HEALTHCARE ENTERPRISE",
      impact: "100% HIPAA & SOC2 Compliant"
    },
    {
      quote: "The multi-cloud auto-fallback saved our customer-facing AI agents during the recent OpenAI service disruption. Traffic switched to Claude Sonnet instantly with zero downtime.",
      author: "David Chen",
      role: "Head of AI Infrastructure",
      company: "Scale SaaS Mesh",
      badge: "AI PLATFORM",
      impact: "99.999% Zero Downtime SLA"
    }
  ];

  return (
    <section id="testimonials" className="py-28 bg-[#FAFAF8] text-slate-900 border-b border-slate-200/80 light-body-pattern">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center space-y-4 max-w-3xl mx-auto mb-20">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-slate-200/80 border border-slate-300 text-xs font-mono font-semibold text-slate-700 tracking-wider uppercase">
            ENTERPRISE TESTIMONIALS
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-tight">
            Trusted by Engineering Leaders.
          </h2>
          <p className="text-slate-600 text-base sm:text-lg leading-relaxed">
            Discover why Fortune 500 enterprises rely on Sentinel for mission-critical AI control plane infrastructure.
          </p>
        </div>

        {/* Testimonial Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((t, idx) => (
            <div
              key={idx}
              className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm light-card-shadow flex flex-col justify-between space-y-6"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="px-3 py-1 rounded-full text-xs font-mono font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                    {t.badge}
                  </span>
                  <Quote className="w-6 h-6 text-slate-300" />
                </div>

                <p className="text-sm sm:text-base text-slate-700 leading-relaxed font-normal italic">
                  "{t.quote}"
                </p>
              </div>

              <div className="pt-6 border-t border-slate-100 space-y-3">
                <div>
                  <div className="font-bold text-slate-900 text-sm font-sans">{t.author}</div>
                  <div className="text-xs text-slate-500">{t.role} • <strong className="text-slate-700">{t.company}</strong></div>
                </div>
                <div className="px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-mono font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>{t.impact}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
