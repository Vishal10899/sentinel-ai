"use client";

import { useEffect, useRef } from "react";
import { Loader2, Square } from "lucide-react";

import { Button, EmptyState } from "../ui";
import MessageBubble from "./MessageBubble";
import MessageInput from "./MessageInput";

export default function ChatWindow({
  messages = [],
  prompt = "",
  onPromptChange,
  onSend,
  onCopy,
  onRetry,
  loading = false,
  stopSupported = false,
}) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, loading]);

  return (
    <div className="flex h-full min-h-[70vh] flex-col">
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4 sm:p-6">
        {messages.length === 0 ? (
          <EmptyState
            title="Start a conversation"
            copy="Choose a model, write a prompt, and Sentinel will persist the exchange."
          />
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

         {loading && (
  <div className="flex items-start gap-3 px-1 py-2">
    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-indigo-500 font-semibold text-white shadow-lg">
      AI
    </div>

    <div className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3">
      <div className="flex items-center gap-2 text-slate-300">
        <Loader2 className="h-4 w-4 animate-spin" />

        <span>Thinking...</span>
      </div>

      <div className="mt-2 flex gap-1">
        <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500"></span>

        <span
          className="h-2 w-2 animate-bounce rounded-full bg-slate-500"
          style={{ animationDelay: ".2s" }}
        ></span>

        <span
          className="h-2 w-2 animate-bounce rounded-full bg-slate-500"
          style={{ animationDelay: ".4s" }}
        ></span>
      </div>

      {!stopSupported && (
        <p className="mt-2 text-xs text-slate-500">
          Waiting for provider response...
        </p>
      )}
    </div>
  </div>
)}

        <div ref={endRef} />
      </div>

      {loading && (
        <div className="px-4 pb-2 text-right">
          <Button
            variant="secondary"
            disabled
            title="This provider does not support request cancellation"
          >
            <Square className="h-4 w-4" />
            Stop unavailable
          </Button>
        </div>
      )}
      <div className="border-t border-white/10" />
      <MessageInput 
        value={prompt}
        onChange={onPromptChange}
        onSend={onSend}
        disabled={loading}
        loading={loading}
      />
    </div>
  );
}