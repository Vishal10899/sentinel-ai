"use client";

import { AlertCircle, Check, Loader2, X } from "lucide-react";

export function Button({ children, className = "", variant = "primary", ...props }) {
  const styles = variant === "primary"
    ? "bg-indigo-500 text-white hover:bg-indigo-400 shadow-lg shadow-indigo-500/20"
    : variant === "ghost" ? "bg-transparent text-slate-300 hover:bg-white/[.06]"
    : "border border-white/10 bg-white/[.05] text-white hover:bg-white/[.09]";
  return <button className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${styles} ${className}`} {...props}>{children}</button>;
}

export function Badge({ children, tone = "slate" }) {
  const tones = { green: "bg-emerald-400/10 text-emerald-300 ring-emerald-400/20", indigo: "bg-indigo-400/10 text-indigo-300 ring-indigo-400/20", amber: "bg-amber-400/10 text-amber-300 ring-amber-400/20", slate: "bg-slate-400/10 text-slate-300 ring-slate-400/20" };
  return <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ${tones[tone]}`}><span className="h-1.5 w-1.5 rounded-full bg-current" />{children}</span>;
}

export function LoadingCard({ label = "Loading data" }) { return <div className="surface flex min-h-40 items-center justify-center gap-2 text-sm text-slate-400"><Loader2 className="h-4 w-4 animate-spin" />{label}</div>; }
export function ErrorCard({ error, retry }) { return <div className="surface flex min-h-40 flex-col items-center justify-center gap-3 p-6 text-center"><AlertCircle className="h-6 w-6 text-rose-300" /><p className="text-sm text-slate-300">{error}</p>{retry && <Button variant="secondary" onClick={retry}>Try again</Button>}</div>; }
export function EmptyState({ title, copy }) { return <div className="surface p-10 text-center"><p className="font-medium">{title}</p><p className="mt-2 text-sm text-slate-400">{copy}</p></div>; }
export function Toast({ message, clear }) { if (!message) return null; return <div className="fixed bottom-5 right-5 z-50 flex max-w-sm items-center gap-3 rounded-xl border border-emerald-400/20 bg-[#101725] px-4 py-3 text-sm text-emerald-200 shadow-2xl"><Check className="h-4 w-4" />{message}<button onClick={clear}><X className="h-4 w-4" /></button></div>; }
