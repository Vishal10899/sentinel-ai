"use client";

import { useState } from "react";
import { ChevronDown, HelpCircle } from "lucide-react";

export default function FaqSection() {
  const [openIndex, setOpenIndex] = useState(0);

  const faqs = [
    {
      q: "What latency impact does Sentinel add to our AI requests?",
      a: "Sentinel's core proxy engine is written in Rust and processes payload inspection, regex DLP, and routing rules in under 2.4 milliseconds. In fact, for cached requests, Sentinel responds in under 0.3ms—making your overall application significantly faster than hitting direct LLM endpoints."
    },
    {
      q: "Does Sentinel log or retain our sensitive application prompt data?",
      a: "No. Sentinel adheres to a zero-data-retention default policy. Payloads are inspected transiently in RAM to perform real-time sanitization and cache lookups, then immediately purged. Audit logs contain cryptographic hashes and redacted metadata only."
    },
    {
      q: "Can Sentinel be deployed in our own private cloud (VPC) or air-gapped data center?",
      a: "Yes. In addition to our multi-region managed cloud service, Sentinel Enterprise is available as a Docker container or Kubernetes Helm chart for deployment inside AWS VPC, Azure VNet, Google Cloud Platform, or air-gapped on-premises environments."
    },
    {
      q: "Do we need to rewrite our application code or replace our existing AI SDKs?",
      a: "Zero code rewrite is required. Sentinel acts as a reverse proxy compatible with standard OpenAI, Anthropic, and LangChain SDKs. You simply update your client's `baseURL` parameter to point to your Sentinel endpoint."
    },
    {
      q: "How does Sentinel handle LLM provider rate limits or sudden downtime?",
      a: "Sentinel's Decision Router continuously monitors provider health. If your primary provider returns an HTTP 429/529 rate limit or experiences high latency, Sentinel instantly reroutes the prompt to an equivalent fallback model defined in your SLA policy."
    },
    {
      q: "Is Sentinel SOC2 Type II, ISO 27001, and HIPAA compliant?",
      a: "Yes. Sentinel maintains SOC2 Type II certification, ISO 27001 compliance, and offers signed Business Associate Agreements (BAA) for healthcare enterprises requiring HIPAA compliance."
    }
  ];

  return (
    <section className="py-28 bg-[#FAFAF8] text-slate-900 border-b border-slate-200/80 light-body-pattern">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center space-y-4 max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-slate-200/80 border border-slate-300 text-xs font-mono font-semibold text-slate-700 tracking-wider uppercase">
            FREQUENTLY ASKED QUESTIONS
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900 leading-tight">
            Everything You Need to Know.
          </h2>
          <p className="text-slate-600 text-base leading-relaxed">
            Got questions about latency, compliance, or architecture? We've got answers.
          </p>
        </div>

        {/* Accordion */}
        <div className="space-y-4">
          {faqs.map((faq, idx) => {
            const isOpen = openIndex === idx;
            return (
              <div
                key={idx}
                className="bg-white border border-slate-200 rounded-xl overflow-hidden light-card-shadow transition-all duration-200"
              >
                <button
                  onClick={() => setOpenIndex(isOpen ? -1 : idx)}
                  className="w-full p-6 text-left flex items-center justify-between gap-4 font-semibold text-base text-slate-900 hover:text-blue-600 transition-colors"
                >
                  <span className="font-sans">{faq.q}</span>
                  <ChevronDown className={`w-5 h-5 text-slate-400 shrink-0 transition-transform duration-200 ${isOpen ? "rotate-180 text-blue-600" : ""}`} />
                </button>

                {isOpen && (
                  <div className="px-6 pb-6 pt-0 text-sm text-slate-600 leading-relaxed border-t border-slate-100 font-normal">
                    {faq.a}
                  </div>
                )}
              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
}
