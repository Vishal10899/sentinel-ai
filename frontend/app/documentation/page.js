"use client";

import { useState } from "react";
import {
  BookOpen,
  Code2,
  Copy,
  Check,
  ExternalLink,
  Search,
  ShieldCheck,
  Zap,
  Cpu,
  ShieldAlert,
  Coins,
  Terminal,
  FileCode,
  Layers,
  ArrowUpRight
} from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Badge, Button, Toast } from "../../components/ui";
import { API_BASE_URL, getApiBaseUrl } from "../../lib/api";

const docSections = [
  {
    id: "overview",
    title: "1. Architecture & Overview",
    icon: ShieldCheck,
    description: "Sentinel AI is a high-availability AI Reverse Proxy and Governance Control Plane.",
    content: `Sentinel AI sits transparently between your applications and LLM providers (Gemini, OpenAI, Anthropic, Ollama). It intercepts prompts in real time to perform model routing, latency benchmarking, token cost calculation, PII guardrail filtering, and semantic caching.`,
    codeExamples: [
      {
        label: "Architecture Flow",
        lang: "bash",
        code: `App Client ---> [ Sentinel AI Control Plane ] ---> Provider APIs
                      |-> Adaptive Router (P95 < 2ms)
                      |-> PII & Secret Scanner
                      |-> Semantic Cache (SHA256)
                      |-> Stream Manager (SSE)`
      }
    ]
  },
  {
    id: "auth",
    title: "2. Authentication & Keys",
    icon: Terminal,
    description: "Secure bearer token authentication and Virtual API Key delegation.",
    content: `All endpoints require standard HTTP Bearer token authentication. Admin credentials generate JWT tokens with workspace scoping and enterprise RBAC policies. Virtual API Keys allow fine-grained rate limits, monthly budgets, and scope restrictions per developer team.`,
    codeExamples: [
      {
        label: "HTTP Authorization Header",
        lang: "http",
        code: `POST /api/v1/chat/stream HTTP/1.1
Host: api.sentinel.ai
Authorization: Bearer sentinel_live_sk_8f9a2b4c1d6e3f5a
Content-Type: application/json`
      }
    ]
  },
  {
    id: "chat-stream",
    title: "3. Chat Streaming (SSE)",
    icon: Zap,
    description: "Real-time Server-Sent Events (SSE) token streaming generator.",
    content: `The /chat/stream endpoint streams response tokens via Server-Sent Events (SSE). Each event emits structured JSON data containing stream session IDs, token deltas, usage statistics, and cost telemetry.`,
    codeExamples: [
      {
        label: "cURL Stream Example",
        lang: "bash",
        code: `curl -N -X POST "http://localhost:8000/api/v1/chat/stream" \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "Explain distributed transaction sagas",
    "strategy": "adaptive",
    "workspace_id": "default"
  }'`
      },
      {
        label: "SSE Event Stream Format",
        lang: "json",
        code: `event: metadata
data: {"stream_id": "92ebdbc0", "provider": "gemini", "model": "gemini-2.0-flash"}

event: token
data: {"token": "Distributed "}

event: token
data: {"token": "sagas "}

event: usage
data: {"prompt_tokens": 12, "completion_tokens": 45, "cost_usd": 0.0003, "latency_ms": 18}

event: done
data: {"status": "completed"}`
      }
    ]
  },
  {
    id: "routing",
    title: "4. Adaptive Model Routing",
    icon: Cpu,
    description: "Automated model selection with real-time score explainability.",
    content: `The Adaptive Router automatically selects the optimal provider model based on task intent, historical latency, cost thresholds, and quality scores. Supported routing strategies include adaptive, cheapest, fastest, highest_quality, and reasoning_optimized.`,
    codeExamples: [
      {
        label: "Explain Route Request",
        lang: "json",
        code: `POST /api/v1/routing/explain
{
  "task_category": "code_generation",
  "strategy": "balanced",
  "prompt_tokens": 120,
  "max_completion_tokens": 500
}`
      }
    ]
  },
  {
    id: "guardrails",
    title: "5. AI Guardrails & PII Interception",
    icon: ShieldAlert,
    description: "Real-time prompt inspection, PII redaction, and secret detection.",
    content: `Sentinel AI inspects every incoming prompt against PII patterns (Social Security Numbers, Credit Cards, API Keys, Passwords) and toxicity policies. Non-compliant prompts are blocked or redacted before touching upstream LLMs.`,
    codeExamples: [
      {
        label: "Simulate Guardrail Scan",
        lang: "json",
        code: `POST /api/v1/guardrails/scan
{
  "prompt": "User SSN is 000-12-3456 and secret API key is sk_live_abc123"
}`
      }
    ]
  },
  {
    id: "cache",
    title: "6. Semantic Prompt Cache",
    icon: Coins,
    description: "Sub-10ms prompt response caching with cost elimination.",
    content: `Identical or semantically equivalent prompts are served directly from the Sentinel in-memory cache, eliminating upstream LLM latency and reducing API costs to $0.00.`,
    codeExamples: [
      {
        label: "Cache Analytics API",
        lang: "http",
        code: `GET /api/v1/cache/stats HTTP/1.1
Authorization: Bearer $TOKEN`
      }
    ]
  }
];

export default function DocumentationPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedId, setCopiedId] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);
  const [activeTab, setActiveTab] = useState("all");

  const openApiUrl = `${getApiBaseUrl().replace("/api/v1", "")}/docs`;

  const copyToClipboard = (code, id) => {
    navigator.clipboard.writeText(code);
    setCopiedId(id);
    setToastMessage("Snippet copied to clipboard!");
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredSections = docSections.filter(
    (sec) =>
      sec.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sec.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sec.content.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <AppShell>
      <div className="space-y-6 max-w-7xl mx-auto">
        {/* Page Title & OpenAPI Banner */}
        <PageTitle
          eyebrow="Developer Center"
          title="Sentinel AI API & Architecture Reference"
          subtitle="Complete reference documentation for integrating the Sentinel AI control plane, reverse proxy, SSE streaming, and routing engine."
          action={
            <a
              href={openApiUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500 transition shadow-md shadow-indigo-600/20"
            >
              <BookOpen className="h-4 w-4" />
              <span>Interactive Swagger Specs</span>
              <ArrowUpRight className="h-3.5 w-3.5" />
            </a>
          }
        />

        {/* Toast Notification */}
        {toastMessage && <Toast type="success" message={toastMessage} onClose={() => setToastMessage(null)} />}

        {/* Documentation Search & Controls Bar */}
        <div className="surface p-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="relative w-full md:w-96">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search documentation, cURL, endpoints..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl border border-[var(--border-color)] bg-[var(--input-bg)] py-2 pl-10 pr-4 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)] outline-none focus:border-indigo-500 transition"
            />
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto">
            {["all", "quickstart", "api", "routing", "security"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition cursor-pointer ${
                  activeTab === tab
                    ? "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.04]"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Main Grid: Left TOC Sidebar + Right Doc Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
          {/* Table of Contents Sticky Sidebar */}
          <aside className="surface p-4 lg:sticky lg:top-20 space-y-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] block px-2">
              Documentation Index
            </span>
            <nav className="space-y-1">
              {docSections.map((sec) => {
                const Icon = sec.icon;
                return (
                  <a
                    key={sec.id}
                    href={`#${sec.id}`}
                    className="flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition"
                  >
                    <Icon className="h-4 w-4 text-indigo-400 shrink-0" />
                    <span className="truncate">{sec.title}</span>
                  </a>
                );
              })}
            </nav>

            <div className="border-t border-[var(--border-color)] pt-3 px-2">
              <span className="text-[11px] text-[var(--text-muted)] block">Base API URL:</span>
              <code className="text-[10px] font-mono text-indigo-400 block mt-1 truncate">{getApiBaseUrl()}</code>
            </div>
          </aside>

          {/* Doc Content Sections */}
          <main className="lg:col-span-3 space-y-6">
            {filteredSections.length === 0 ? (
              <div className="surface p-12 text-center space-y-2">
                <Search className="h-8 w-8 text-[var(--text-muted)] mx-auto" />
                <p className="text-sm font-bold text-[var(--text-primary)]">No matching documentation sections found</p>
                <p className="text-xs text-[var(--text-secondary)]">Try searching for keywords like "stream", "routing", "PII", or "cURL".</p>
              </div>
            ) : (
              filteredSections.map((section) => {
                const Icon = section.icon;
                return (
                  <section
                    key={section.id}
                    id={section.id}
                    className="surface p-6 space-y-4 scroll-mt-24"
                  >
                    <div className="flex items-start justify-between gap-4 border-b border-[var(--border-color)] pb-4">
                      <div className="flex items-center gap-3">
                        <div className="rounded-xl bg-indigo-500/10 border border-indigo-500/20 p-2.5 text-indigo-400">
                          <Icon className="h-5 w-5" />
                        </div>
                        <div>
                          <h2 className="text-base font-bold text-[var(--text-primary)] tracking-tight">{section.title}</h2>
                          <p className="text-xs text-[var(--text-secondary)] mt-0.5">{section.description}</p>
                        </div>
                      </div>
                      <Badge variant="indigo">V1 API</Badge>
                    </div>

                    <p className="text-xs leading-relaxed text-[var(--text-secondary)]">{section.content}</p>

                    {/* Code Snippet Block */}
                    {section.codeExamples?.map((eg, idx) => (
                      <div key={idx} className="space-y-2">
                        <div className="flex items-center justify-between px-1">
                          <span className="text-[11px] font-mono font-semibold text-[var(--text-muted)] flex items-center gap-1.5">
                            <FileCode className="h-3.5 w-3.5 text-indigo-400" />
                            {eg.label}
                          </span>
                          <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase">{eg.lang}</span>
                        </div>

                        <div className="relative rounded-xl border border-slate-800 bg-[#0f172a] p-4 text-slate-100 font-mono text-xs overflow-x-auto shadow-xl">
                          <button
                            onClick={() => copyToClipboard(eg.code, `${section.id}-${idx}`)}
                            className="absolute top-3 right-3 flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-2.5 py-1 text-[11px] font-semibold text-slate-300 hover:bg-slate-700 hover:text-white transition cursor-pointer"
                          >
                            {copiedId === `${section.id}-${idx}` ? (
                              <>
                                <Check className="h-3.5 w-3.5 text-emerald-400" />
                                <span className="text-emerald-400">Copied!</span>
                              </>
                            ) : (
                              <>
                                <Copy className="h-3.5 w-3.5" />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                          <pre className="pr-16 leading-relaxed whitespace-pre font-mono text-[11px]">{eg.code}</pre>
                        </div>
                      </div>
                    ))}
                  </section>
                );
              })
            )}
          </main>
        </div>
      </div>
    </AppShell>
  );
}
