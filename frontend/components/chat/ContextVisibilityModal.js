"use client";

import { X, FileText, CheckCircle2, Copy, Hash, Layers, ShieldCheck, Database } from "lucide-react";
import { Badge, Button } from "../ui";

export default function ContextVisibilityModal({ isOpen, onClose, attachment }) {
  if (!isOpen || !attachment) return null;

  const copyText = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      alert("Extracted text copied to clipboard!");
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-xl rounded-2xl border border-white/10 bg-[#111827] shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-4 bg-white/[0.02]">
          <div className="flex items-center gap-2 text-indigo-400">
            <FileText className="h-5 w-5" />
            <h2 className="text-sm font-bold text-white truncate max-w-[320px]">{attachment.filename}</h2>
          </div>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-white/10">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-4 overflow-y-auto flex-1">
          {/* Status & Format Badges */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="flex items-center gap-1 rounded-full bg-emerald-500/10 px-3 py-1 font-semibold text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="h-3.5 w-3.5" /> Extraction Status: Processed
            </span>
            {attachment.extension && (
              <span className="rounded-full bg-indigo-500/10 px-3 py-1 font-mono uppercase font-bold text-indigo-300 border border-indigo-500/20">
                {attachment.extension}
              </span>
            )}
            {attachment.is_duplicate && (
              <span className="rounded-full bg-amber-500/10 px-3 py-1 font-semibold text-amber-300 border border-amber-500/20">
                Duplicate Hash Detected
              </span>
            )}
          </div>

          {/* Stats Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div className="rounded-xl border border-white/10 bg-black/30 p-3">
              <p className="text-[10px] uppercase font-bold text-slate-400">Word Count</p>
              <p className="text-sm font-bold text-white mt-0.5">{(attachment.word_count || 0).toLocaleString()}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-black/30 p-3">
              <p className="text-[10px] uppercase font-bold text-slate-400">Characters</p>
              <p className="text-sm font-bold text-white mt-0.5">{(attachment.character_count || attachment.size_bytes || 0).toLocaleString()}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-black/30 p-3">
              <p className="text-[10px] uppercase font-bold text-slate-400">Est. Tokens</p>
              <p className="text-sm font-bold text-indigo-300 mt-0.5">{(attachment.estimated_tokens || Math.ceil((attachment.size_bytes || 0)/4)).toLocaleString()}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-black/30 p-3">
              <p className="text-[10px] uppercase font-bold text-slate-400">Chunks</p>
              <p className="text-sm font-bold text-emerald-300 mt-0.5">{attachment.chunk_count || 1}</p>
            </div>
          </div>

          {/* SHA-256 Security Hash */}
          {attachment.sha256_hash && (
            <div className="rounded-xl border border-white/10 bg-black/20 p-3 text-xs">
              <div className="flex items-center gap-1.5 font-semibold text-slate-300 mb-1">
                <Hash className="h-3.5 w-3.5 text-indigo-400" /> SHA-256 Security Fingerprint
              </div>
              <p className="font-mono text-[10px] text-slate-400 break-all">{attachment.sha256_hash}</p>
            </div>
          )}

          {/* Extracted Text Preview */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
              <span className="flex items-center gap-1">
                <Layers className="h-3.5 w-3.5 text-indigo-400" /> Document Context Snippet
              </span>
              <button
                onClick={() => copyText(attachment.extracted_text || "")}
                className="flex items-center gap-1 text-[11px] text-indigo-300 hover:text-white"
              >
                <Copy className="h-3 w-3" /> Copy Context
              </button>
            </div>
            <div className="max-h-48 overflow-y-auto rounded-xl border border-white/10 bg-black/40 p-3 font-mono text-[11px] text-slate-300 whitespace-pre-wrap leading-relaxed">
              {attachment.extracted_text || "[No extractable plain text text content found]"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
