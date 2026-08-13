"use client";

import { 
  Check, 
  ArrowRight, 
  ShieldCheck, 
  Zap, 
  Building2 
} from "lucide-react";

export default function PricingSection() {
  const plans = [
    {
      name: "Developer",
      badge: "FREE FOREVER",
      price: "$0",
      period: "/ month",
      desc: "Essential control plane for small projects, staging environments, and individual builders.",
      features: [
        "Up to 1,000,000 requests / mo",
        "Sub-millisecond Semantic Cache",
        "Basic PII & DLP sanitization",
        "OpenAI & Anthropic Proxy Routing",
        "Community Discord support",
        "Single user access key"
      ],
      cta: "Start Free",
      highlighted: false,
      ctaClass: "bg-slate-900 hover:bg-slate-800 text-white"
    },
    {
      name: "Team & Growth",
      badge: "MOST POPULAR",
      price: "$299",
      period: "/ month",
      desc: "Full governance, latency routing, and cost optimization for fast-scaling engineering teams.",
      features: [
        "Up to 25,000,000 requests / mo",
        "Advanced Prompt Injection Firewall",
        "SLA-Aware Multi-Cloud Fallback",
        "Custom Regex & PII Redaction Rules",
        "OpenTelemetry Datadog / Prometheus Export",
        "Up to 10 Virtual API Keys",
        "99.9% Uptime Guarantee SLA"
      ],
      cta: "Deploy Team Proxy",
      highlighted: true,
      ctaClass: "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/30"
    },
    {
      name: "Enterprise VPC",
      badge: "CUSTOM / ON-PREM",
      price: "Custom",
      period: "",
      desc: "Dedicated control plane deployed within your AWS, Azure, or GCP private cloud perimeters.",
      features: [
        "Unlimited Request Throughput",
        "Air-Gapped & VPC On-Premises Deployment",
        "Custom Fine-Tuned Local Router",
        "24/7 Dedicated Solutions Engineer",
        "Custom Security & Audit SLAs (99.999%)",
        "SSO, SAML, Fine-Grained RBAC",
        "HIPAA BAA & SOC2 Audit Reports"
      ],
      cta: "Contact Enterprise Sales",
      highlighted: false,
      ctaClass: "bg-slate-900 hover:bg-slate-800 text-white"
    }
  ];

  return (
    <section id="pricing" className="py-28 bg-[#F8F7F2] text-slate-900 border-b border-slate-200/80 light-body-pattern">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center space-y-4 max-w-3xl mx-auto mb-20">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-slate-200/80 border border-slate-300 text-xs font-mono font-semibold text-slate-700 tracking-wider uppercase">
            TRANSPARENT ENTERPRISE PRICING
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-tight">
            Predictable Control Plane Economics.
          </h2>
          <p className="text-slate-600 text-base sm:text-lg leading-relaxed">
            Choose the deployment model that fits your enterprise security and throughput needs.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan, idx) => (
            <div
              key={idx}
              className={`bg-white rounded-2xl p-8 shadow-sm flex flex-col justify-between relative transition-all duration-200 ${
                plan.highlighted 
                  ? "border-2 border-blue-600 shadow-xl ring-4 ring-blue-500/10" 
                  : "border border-slate-200 light-card-shadow"
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-blue-600 text-[10px] font-mono font-bold text-white uppercase tracking-widest shadow-md">
                  RECOMMENDED FOR TEAMS
                </div>
              )}

              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-slate-500 tracking-wider uppercase">
                    {plan.badge}
                  </span>
                </div>

                <div>
                  <h3 className="text-2xl font-bold text-slate-900 font-sans">{plan.name}</h3>
                  <div className="flex items-baseline gap-1 mt-2">
                    <span className="text-4xl sm:text-5xl font-extrabold text-slate-900 font-mono tracking-tight">{plan.price}</span>
                    <span className="text-sm font-medium text-slate-500">{plan.period}</span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed mt-2">{plan.desc}</p>
                </div>

                <div className="pt-6 border-t border-slate-100 space-y-3">
                  <div className="text-xs font-mono font-bold uppercase text-slate-400">WHAT'S INCLUDED</div>
                  {plan.features.map((feat, fIdx) => (
                    <div key={fIdx} className="flex items-center gap-2.5 text-xs text-slate-700 font-medium">
                      <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span>{feat}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-8">
                <a
                  href="/register"
                  className={`w-full py-3 px-4 rounded-xl font-medium text-xs text-center flex items-center justify-center gap-2 transition-all duration-200 ${plan.ctaClass}`}
                >
                  <span>{plan.cta}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
