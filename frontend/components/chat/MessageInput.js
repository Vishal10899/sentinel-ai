"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import { Loader2, Paperclip, Send, X, FileText, Image as ImageIcon, Sparkles, BookOpen, Terminal, Info } from "lucide-react";
import { Button } from "../ui";
import { api } from "../../lib/api";
import ContextVisibilityModal from "./ContextVisibilityModal";

const SLASH_COMMANDS = [
  { command: "/summarize", description: "Summarize text or attached document", prompt: "Summarize the following text or attached document into key takeaways:" },
  { command: "/fix-code", description: "Debug and fix code errors", prompt: "Please review the following code for bugs, errors, and performance issues, then provide the fixed version:" },
  { command: "/explain", description: "Explain complex concepts step-by-step", prompt: "Explain the following concept in clear, simple, step-by-step terms with real-world examples:" },
  { command: "/refactor", description: "Clean code & improve architecture", prompt: "Refactor the following code to adhere to clean code principles, DRY design, and modern best practices:" },
  { command: "/security-audit", description: "Audit for security vulnerabilities", prompt: "Perform a security audit on the following code/input. Identify vulnerabilities, risks, and mitigations:" },
];

export default function MessageInput({
  value = "",
  onChange,
  onSend,
  onStop,
  disabled = false,
  loading = false,
  attachments = [],
  onAttachmentsChange,
  onOpenPromptLibrary,
  activeMode = "chat",
  onModeChange,
}) {
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [showSlashMenu, setShowSlashMenu] = useState(false);
  const [selectedAttachmentForModal, setSelectedAttachmentForModal] = useState(null);

  useEffect(() => {
    const element = textareaRef.current;
    if (!element) return;
    element.style.height = "auto";
    element.style.height = `${Math.min(element.scrollHeight, 180)}px`;

    // Show slash menu if input starts with '/'
    if (value.startsWith("/") && !value.includes(" ")) {
      setShowSlashMenu(true);
    } else {
      setShowSlashMenu(false);
    }
  }, [value]);

  const estimatedTokens = useMemo(() => {
    return Math.max(Math.ceil(value.length / 4), 0);
  }, [value]);

  const handleSend = () => {
    const message = value.trim();
    if (!message || disabled || loading || uploading) return;
    onSend?.();
    setShowSlashMenu(false);
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  const handleSelectSlashCommand = (cmd) => {
    onChange?.(cmd.prompt);
    setShowSlashMenu(false);
    textareaRef.current?.focus();
  };

  const handlePaste = async (event) => {
    const items = event.clipboardData?.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.kind === "file") {
        const file = item.getAsFile();
        if (file) {
          event.preventDefault();
          setUploading(true);
          try {
            const uploaded = await api.uploadFile(file);
            onAttachmentsChange?.([...attachments, uploaded]);
          } catch (err) {
            alert(`Paste upload failed: ${err.message}`);
          } finally {
            setUploading(false);
          }
        }
      }
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const uploaded = await api.uploadFile(file);
      onAttachmentsChange?.([...attachments, uploaded]);
    } catch (err) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const removeAttachment = (id) => {
    onAttachmentsChange?.(attachments.filter((a) => a.id !== id));
  };

  return (
    <div className="relative border-t border-[var(--border-color)] p-3 sm:p-4 bg-[var(--bg-secondary)]">
      {/* Requirement 8: Mode Selection Segmented Control near Composer */}
      <div className="flex items-center gap-1 overflow-x-auto mb-2 pb-0.5 no-scrollbar">
        {["Chat", "Search", "Create", "Analyze", "Code", "Document", "Agent"].map((modeName) => {
          const mId = modeName.toLowerCase();
          const isActive = (activeMode || "chat") === mId;
          return (
            <button
              key={mId}
              type="button"
              onClick={() => onModeChange?.(mId)}
              className={`px-2.5 py-0.5 rounded-lg text-[11px] font-semibold transition cursor-pointer shrink-0 ${
                isActive
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "bg-[var(--bg-surface)] text-[var(--text-muted)] hover:bg-indigo-500/10 hover:text-indigo-400 border border-[var(--border-color)]"
              }`}
            >
              {modeName}
            </button>
          );
        })}
      </div>
      {/* Slash Command Suggestions Popup */}
      {showSlashMenu && (
        <div className="absolute bottom-full left-4 mb-2 z-40 w-80 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-elevated)] p-2 shadow-2xl">
          <div className="flex items-center gap-1 px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-amber-500">
            <Terminal className="h-3 w-3" /> Slash Commands
          </div>
          <div className="space-y-1 mt-1">
            {SLASH_COMMANDS.map((cmd) => (
              <button
                key={cmd.command}
                onClick={() => handleSelectSlashCommand(cmd)}
                className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left hover:bg-[var(--bg-surface)] transition cursor-pointer"
              >
                <div>
                  <p className="text-xs font-semibold text-indigo-400">{cmd.command}</p>
                  <p className="text-[10px] text-[var(--text-secondary)]">{cmd.description}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Attachment Previews */}
      {attachments.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {attachments.map((att) => (
            <div
              key={att.id}
              className="flex items-center gap-1.5 rounded-xl border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-1 text-xs text-indigo-400 font-medium"
            >
              {att.content_type?.includes("image") ? (
                <ImageIcon className="h-3.5 w-3.5 text-indigo-400" />
              ) : (
                <FileText className="h-3.5 w-3.5 text-indigo-400" />
              )}
              <span className="max-w-[150px] truncate">{att.filename}</span>
              {att.chunk_count && (
                <span className="text-[10px] font-mono text-emerald-500 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                  {att.chunk_count} chunks
                </span>
              )}
              <button
                onClick={() => setSelectedAttachmentForModal(att)}
                className="text-indigo-400 hover:text-indigo-300 p-0.5"
                title="View document metadata & chunks"
              >
                <Info className="h-3.5 w-3.5" />
              </button>
              <button onClick={() => removeAttachment(att.id)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] p-0.5">
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      <ContextVisibilityModal
        isOpen={!!selectedAttachmentForModal}
        onClose={() => setSelectedAttachmentForModal(null)}
        attachment={selectedAttachmentForModal}
      />

      <div className="flex items-end gap-2">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          className="hidden"
          accept=".txt,.md,.csv,.json,.pdf,.docx,.png,.jpg,.jpeg,.webp"
        />

        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="flex h-12 w-12 items-center justify-center rounded-xl border border-[var(--border-color)] bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:border-indigo-500/50 hover:text-[var(--text-primary)] disabled:opacity-50 transition cursor-pointer"
          title="Attach PDF, DOCX, TXT, CSV, or Image"
        >
          {uploading ? <Loader2 className="h-4 w-4 animate-spin text-indigo-400" /> : <Paperclip className="h-4 w-4" />}
        </button>

        {onOpenPromptLibrary && (
          <button
            type="button"
            onClick={onOpenPromptLibrary}
            className="flex h-12 w-12 items-center justify-center rounded-xl border border-[var(--border-color)] bg-[var(--bg-surface)] text-indigo-400 hover:border-indigo-500/50 hover:bg-indigo-500/10 transition cursor-pointer"
            title="Open Prompt Library"
          >
            <BookOpen className="h-4 w-4" />
          </button>
        )}

        <textarea
          ref={textareaRef}
          rows={1}
          maxLength={32000}
          value={value}
          placeholder="Message Sentinel AI or type '/' for commands..."
          className="min-h-12 max-h-44 flex-1 resize-none rounded-xl border border-[var(--border-color)] bg-[var(--input-bg)] px-3.5 py-3 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] outline-none ring-indigo-500/40 focus:ring-2 focus:border-indigo-500 transition"
          onChange={(event) => onChange?.(event.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
        />

        <Button
          onClick={handleSend}
          disabled={loading || uploading || (value.trim().length === 0 && attachments.length === 0)}
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          Send
        </Button>
      </div>

      <div className="mt-2 flex items-center justify-between text-[11px] text-[var(--text-muted)]">
        <span className="flex items-center gap-1">
          <span>Enter to send · Shift+Enter newline · Type <strong>/</strong> for commands</span>
        </span>
        <div className="flex items-center gap-3">
          {estimatedTokens > 0 && (
            <span className="font-mono text-indigo-400">~{estimatedTokens} tokens</span>
          )}
          <span>{value.length.toLocaleString()}/32,000</span>
        </div>
      </div>
    </div>
  );
}