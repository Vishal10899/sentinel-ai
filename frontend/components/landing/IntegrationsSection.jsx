"use client";

import { 
  Cpu, 
  Globe, 
  Server, 
  Database, 
  ShieldCheck, 
  Activity, 
  Layers, 
  Code2 
} from "lucide-react";

export default function IntegrationsSection() {
  const integrations = [
    { category: "AI LLM Providers", items: ["OpenAI GPT-4o", "Anthropic Claude 3.5", "AWS Bedrock", "Google Vertex AI", "Azure OpenAI", "DeepSeek R1/V3", "Groq Llama 3.3", "Ollama Local"] },
    { category: "Application Frameworks", items: ["LangChain", "LlamaIndex", "Next.js / Vercel", "Python SDK", "Node.js / TS", "Go SDK", "Java Enterprise", "Rust Core"] },
    { category: "Observability & SIEM", items: ["Datadog", "Prometheus", "Grafana", "Splunk", "New Relic", "OpenTelemetry", "Elasticsearch", "AWS CloudWatch"] }
  ];

  return (
    <section id="integrations" className="py-28 bg-[#FAFAF8] text-slate-900 border-b border-slate-200/80 light-body-pattern">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center space-y-4 max-w-3xl mx-auto mb-20">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-slate-200/80 border border-slate-300 text-xs font-mono font-semibold text-slate-700 tracking-wider uppercase">
            ENTERPRISE ECOSYSTEM
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-tight">
            Seamless Plug & Play Integration.
          </h2>
          <p className="text-slate-600 text-base sm:text-lg leading-relaxed">
            Sentinel integrates natively with your existing application code, cloud security stacks, and model provider subscriptions.
          </p>
        </div>

        {/* Integration Categories Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {integrations.map((cat, idx) => (
            <div
              key={idx}
              className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm light-card-shadow space-y-6"
            >
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <h3 className="font-bold text-lg text-slate-900 font-sans">{cat.category}</h3>
                <span className="text-xs font-mono text-blue-600 font-semibold">{cat.items.length} CONNECTORS</span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {cat.items.map((item, itemIdx) => (
                  <div
                    key={itemIdx}
                    className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 hover:bg-slate-100/80 transition-colors text-xs font-medium text-slate-800 flex items-center gap-2"
                  >
                    <div className="w-2 h-2 rounded-full bg-blue-500 shrink-0" />
                    <span className="truncate">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
