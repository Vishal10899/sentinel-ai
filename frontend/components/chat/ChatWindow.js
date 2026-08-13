"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, Square, Zap, Sparkles, Code, FileText, ShieldCheck, Database, ArrowDown, Cpu, Coins, ShieldAlert, Layers } from "lucide-react";

import { Button, EmptyState } from "../ui";
import MessageBubble from "./MessageBubble";
import MessageInput from "./MessageInput";

const SUGGESTED_PROMPTS = [
  { icon: Code, title: "Review & Optimize Code", prompt: "Review the following code for performance bottlenecks, edge cases, and security vulnerabilities:" },
  { icon: FileText, title: "Executive Document Summary", prompt: "Summarize the key findings and actionable takeaways from the attached document:" },
  { icon: ShieldCheck, title: "Security Vulnerability Audit", prompt: "Audit the following software module for security flaws, input validation gaps, and OWASP risks:" },
  { icon: Database, title: "SQL Query Performance Tune", prompt: "Analyze this SQL query for index usage, execution bottlenecks, and suggest an optimized query structure:" },
];

const FEATURE_CARDS = [
  { icon: Cpu, title: "Adaptive Routing", desc: "Selects optimal LLM (Gemini, OpenAI, Anthropic, Ollama) based on P95 latency & cost." },
  { icon: Coins, title: "Cost Optimization", desc: "Sub-10ms responses with automated cost elimination and token budgeting." },
  { icon: ShieldAlert, title: "AI Guardrails", desc: "Intercepts PII, SSNs, credit cards, and secret API keys in real time." },
  { icon: Layers, title: "Semantic Cache", desc: "In-memory prompt-response cache delivering $0.00 sub-10ms answers." },
];

export default function ChatWindow({
  messages = [],
  prompt = "",
  attachments = [],
  onAttachmentsChange,
  onPromptChange,
  onSend,
  onStop,
  onCopy,
  onRetry,
  onOpenPromptLibrary,
  loading = false,
  isModelLoadingVram = false,
  streamStats = null,
  activeMode = "chat",
  onModeChange,
}) {
  console.log("[Frontend] React render triggered | Messages:", messages.length);
  const containerRef = useRef(null);
  const endRef = useRef(null);
  const userScrolledUp = useRef(false);
  const [showJumpToBottom, setShowJumpToBottom] = useState(false);

  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isNearBottom = scrollHeight - (scrollTop + clientHeight) < 120;
    userScrolledUp.current = !isNearBottom;
    setShowJumpToBottom(!isNearBottom);
  };

  const scrollToBottom = () => {
    userScrolledUp.current = false;
    setShowJumpToBottom(false);
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  };

  useEffect(() => {
    if (!userScrolledUp.current) {
      endRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }
  }, [messages, loading]);

  const handleSelectSuggestedPrompt = (suggestedPromptText) => {
    onPromptChange?.(suggestedPromptText);
  };

  return (
    <div className="relative flex flex-1 min-h-0 w-full flex-col overflow-hidden bg-[var(--bg-secondary)]">
      {/* Stream Telemetry Header Bar */}
      {loading && streamStats && (
        <div className="shrink-0 flex items-center justify-between border-b border-indigo-500/20 bg-indigo-500/10 px-4 py-2 text-[11px] text-indigo-400 font-mono">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 font-semibold text-emerald-500">
              <Zap className="h-3 w-3 animate-pulse" /> STREAMING
            </span>
            <span>Provider: <strong>{streamStats.provider || "Auto"}</strong></span>
            <span>Model: <strong>{streamStats.model || "Selected"}</strong></span>
            {streamStats.tokensPerSec > 0 && (
              <span>Speed: <strong>{streamStats.tokensPerSec} t/s</strong></span>
            )}
          </div>
          {onStop && (
            <button
              onClick={onStop}
              className="flex items-center gap-1 rounded-lg bg-rose-500/20 px-2.5 py-1 font-semibold text-rose-400 hover:bg-rose-500/30 transition cursor-pointer"
            >
              <Square className="h-3 w-3 fill-rose-400" /> Stop Generating
            </button>
          )}
        </div>
      )}

      {/* Main Scrollable Messages / Welcome Area */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="min-h-0 flex-1 overflow-y-auto p-4 sm:p-6 scroll-smooth"
      >
        <div className="max-w-4xl mx-auto space-y-6 w-full">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center text-center py-6 sm:py-10 my-auto max-w-3xl mx-auto space-y-6">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 shadow-sm">
                <Sparkles className="h-7 w-7" />
              </div>

              <div>
                <h2 className="text-xl font-bold text-[var(--text-primary)] tracking-tight">Welcome to Sentinel AI Workspace</h2>
                <p className="text-xs text-[var(--text-secondary)] max-w-lg mx-auto mt-1.5 leading-relaxed">
                  Enterprise AI Gateway. Route prompts dynamically, enforce guardrails, and audit cost telemetry in real time.
                </p>
              </div>

              {/* 4 Feature Architecture Cards Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
                {FEATURE_CARDS.map((fc, idx) => {
                  const Icon = fc.icon;
                  return (
                    <div
                      key={idx}
                      className="p-3.5 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-surface)] space-y-1 shadow-sm"
                    >
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400">
                          <Icon className="h-4 w-4" />
                        </div>
                        <h4 className="text-xs font-bold text-[var(--text-primary)]">{fc.title}</h4>
                      </div>
                      <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">{fc.desc}</p>
                    </div>
                  );
                })}
              </div>

              {/* Suggested Starter Prompts Chips Grid */}
              <div className="space-y-2 w-full pt-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)] block text-left">
                  Suggested Starter Prompts
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full text-left">
                  {SUGGESTED_PROMPTS.map((sp, idx) => {
                    const Icon = sp.icon;
                    return (
                      <button
                        key={idx}
                        onClick={() => handleSelectSuggestedPrompt(sp.prompt)}
                        className="group flex items-start gap-2.5 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-surface)] p-3 hover:border-indigo-500/40 hover:bg-indigo-500/5 transition shadow-sm cursor-pointer"
                      >
                        <Icon className="h-4 w-4 shrink-0 text-indigo-400 mt-0.5 group-hover:scale-110 transition-transform" />
                        <div>
                          <h4 className="text-xs font-semibold text-[var(--text-primary)] group-hover:text-indigo-400">{sp.title}</h4>
                          <p className="text-[11px] text-[var(--text-secondary)] line-clamp-1 mt-0.5">{sp.prompt}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <MessageBubble
                key={`${message?.created_at ?? index}-${index}`}
                message={message}
                onCopy={onCopy}
                onRetry={
                  message?.role === "assistant" ? () => onRetry?.(message) : undefined
                }
              />
            ))
          )}

          <div ref={endRef} />
        </div>
      </div>

      {/* Floating Jump to Latest Button */}
      {showJumpToBottom && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-24 right-8 z-30 flex items-center gap-1.5 rounded-full border border-[var(--border-color)] bg-[var(--bg-elevated)] px-3.5 py-1.5 text-xs font-semibold text-[var(--text-primary)] shadow-xl hover:border-indigo-500 transition cursor-pointer"
        >
          <ArrowDown className="h-3.5 w-3.5 text-indigo-400" />
          <span>Jump to latest</span>
        </button>
      )}

      {/* Sticky Message Composer Input Area */}
      <div className="shrink-0 border-t border-[var(--border-color)] bg-[var(--bg-primary)] z-10">
        <MessageInput
          value={prompt}
          attachments={attachments}
          onAttachmentsChange={onAttachmentsChange}
          onChange={onPromptChange}
          onSend={onSend}
          onStop={onStop}
          onOpenPromptLibrary={onOpenPromptLibrary}
          disabled={loading}
          loading={loading}
          activeMode={activeMode}
          onModeChange={onModeChange}
        />
      </div>
    </div>
  );
}