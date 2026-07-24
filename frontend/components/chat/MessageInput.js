"use client";

import { useEffect, useRef } from "react";
import { Loader2, Send } from "lucide-react";

import { Button } from "../ui";

export default function MessageInput({
  value = "",
  onChange,
  onSend,
  disabled = false,
  loading = false,
}) {
  const textareaRef = useRef(null);

  useEffect(() => {
    const element = textareaRef.current;

    if (!element) return;

    element.style.height = "auto";
    element.style.height = `${Math.min(element.scrollHeight, 180)}px`;
  }, [value]);

  const handleSend = () => {
    const message = value.trim();

    if (!message || disabled || loading) return;

    onSend?.();
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-white/[.07] p-4">
      <div className="flex items-end gap-3">
        <textarea
          ref={textareaRef}
          rows={1}
          maxLength={32000}
          value={value}
          disabled={disabled}
          placeholder="Message the selected model..."
          className="min-h-12 max-h-44 flex-1 resize-none rounded-xl border border-white/10 bg-black/20 px-3 py-3 text-sm outline-none ring-indigo-400/40 focus:ring-2 disabled:cursor-not-allowed disabled:opacity-60"
          onChange={(event) => onChange?.(event.target.value)}
          onKeyDown={handleKeyDown}
        />

        <Button
          onClick={handleSend}
          disabled={disabled || loading || value.trim().length === 0}
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
          Send
        </Button>
      </div>

      <div className="mt-2 flex justify-between text-xs text-slate-500">
        <span>Enter to send · Shift+Enter for new line</span>

        <span>{value.length.toLocaleString()}/32,000</span>
      </div>
    </div>
  );
}