"use client";

import Link from "next/link";
import { AlertCircle, CheckCircle2, Loader2, Sparkles, X, ArrowRight, HelpCircle, RefreshCw } from "lucide-react";

export function Button({ children, className = "", variant = "primary", size = "md", isLoading = false, disabled = false, ...props }) {
  const sizeStyles = {
    sm: "px-2.5 py-1.5 text-xs font-semibold rounded-lg",
    md: "px-3.5 py-2 text-xs font-semibold rounded-xl",
    lg: "px-5 py-2.5 text-sm font-bold rounded-xl",
  };

  const variantStyles = {
    primary:
      "bg-indigo-600 text-white hover:bg-indigo-500 active:bg-indigo-700 shadow-md shadow-indigo-600/20 border border-indigo-500/40",
    secondary:
      "bg-[var(--bg-surface)] text-[var(--text-primary)] hover:border-[var(--border-hover)] border border-[var(--border-color)]",
    ghost:
      "bg-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.06]",
    zinc:
      "bg-[var(--bg-elevated)] text-[var(--text-primary)] hover:border-[var(--border-hover)] border border-[var(--border-color)]",
    rose:
      "bg-rose-600 text-white hover:bg-rose-500 shadow-md shadow-rose-600/20 border border-rose-500/40",
    emerald:
      "bg-emerald-600 text-white hover:bg-emerald-500 shadow-md shadow-emerald-600/20 border border-emerald-500/40",
  };

  const selectedSize = sizeStyles[size] || sizeStyles.md;
  const selectedVariant = variantStyles[variant] || variantStyles.primary;

  return (
    <button
      disabled={disabled || isLoading}
      className={`inline-flex items-center justify-center gap-2 transition-all duration-150 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed select-none ${selectedSize} ${selectedVariant} ${className}`}
      {...props}
    >
      {isLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
      {children}
    </button>
  );
}

export function Badge({ children, variant = "emerald", tone, className = "" }) {
  const effectiveVariant = tone === "green" ? "emerald" : tone === "indigo" ? "indigo" : tone === "amber" ? "amber" : tone === "rose" ? "rose" : variant;

  const variants = {
    emerald: "bg-emerald-500/10 text-emerald-500 border-emerald-500/25",
    indigo: "bg-indigo-500/10 text-indigo-400 border-indigo-500/25",
    amber: "bg-amber-500/10 text-amber-500 border-amber-500/25",
    rose: "bg-rose-500/10 text-rose-500 border-rose-500/25",
    zinc: "bg-slate-500/10 text-slate-400 border-slate-500/20",
    cyan: "bg-cyan-500/10 text-cyan-400 border-cyan-500/25",
  };

  const selected = variants[effectiveVariant] || variants.zinc;

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[11px] font-medium font-mono tracking-tight ${selected} ${className}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current opacity-80" />
      {children}
    </span>
  );
}

export function SkeletonCard({ height = "h-48" }) {
  return (
    <div className={`surface ${height} w-full animate-pulse p-6 flex flex-col justify-between`}>
      <div className="space-y-3">
        <div className="h-4 w-1/3 bg-[var(--border-color)] rounded" />
        <div className="h-8 w-2/3 bg-[var(--border-color)] rounded" />
      </div>
      <div className="h-3 w-1/2 bg-[var(--border-color)] rounded" />
    </div>
  );
}

export function LoadingCard({ title = "Loading Telemetry Data...", label }) {
  const text = label || title;
  return (
    <div className="surface flex min-h-[220px] flex-col items-center justify-center gap-3 p-8 text-center">
      <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
      <p className="text-xs font-semibold text-[var(--text-secondary)] font-mono tracking-wide">{text}</p>
    </div>
  );
}

export function ErrorCard({ title = "Data Load Failure", message, error, onRetry, retry }) {
  const errMsg = message || error || "An unexpected error occurred while processing telemetry data.";
  const handleRetry = onRetry || retry;

  return (
    <div className="surface border border-rose-500/30 bg-rose-950/20 flex min-h-[200px] flex-col items-center justify-center gap-3 p-8 text-center">
      <div className="rounded-xl bg-rose-500/10 p-3 text-rose-400 border border-rose-500/20">
        <AlertCircle className="h-6 w-6" />
      </div>
      <div className="space-y-1">
        <h4 className="text-sm font-bold text-[var(--text-primary)]">{title}</h4>
        <p className="text-xs text-rose-300 max-w-md font-mono">{errMsg}</p>
      </div>
      {handleRetry && (
        <Button variant="secondary" size="sm" onClick={handleRetry} className="mt-2">
          <RefreshCw className="h-3.5 w-3.5" /> Retry Request
        </Button>
      )}
    </div>
  );
}

export function EmptyState({ icon: Icon = Sparkles, title = "No Records Found", copy, description, actionText, onAction, docLink = "/documentation" }) {
  const descText = copy || description || "There are no records matching the requested filter in this control plane workspace.";

  return (
    <div className="surface flex flex-col items-center justify-center gap-4 p-10 text-center">
      <div className="rounded-2xl bg-indigo-500/10 p-4 border border-indigo-500/20 text-indigo-400">
        <Icon className="h-7 w-7" />
      </div>
      <div className="space-y-1 max-w-md">
        <h4 className="text-sm font-bold text-[var(--text-primary)] tracking-tight">{title}</h4>
        <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{descText}</p>
      </div>
      <div className="flex items-center gap-3 pt-2">
        {onAction && actionText && (
          <Button size="sm" onClick={onAction}>
            {actionText} <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        )}
        {docLink && (
          <Link href={docLink} className="text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] flex items-center gap-1">
            <HelpCircle className="h-3.5 w-3.5" /> Learn More
          </Link>
        )}
      </div>
    </div>
  );
}

export function Toast({ message, type = "success", clear, onClose }) {
  const handleClose = clear || onClose;
  if (!message) return null;

  const isError = type === "error";

  return (
    <div className={`fixed bottom-6 right-6 z-50 flex max-w-md items-center justify-between gap-3 rounded-xl border px-4 py-3 text-xs font-semibold shadow-2xl backdrop-blur-md transition-all ${
      isError
        ? "border-rose-500/30 bg-[var(--bg-surface)] text-rose-400"
        : "border-emerald-500/30 bg-[var(--bg-surface)] text-emerald-400"
    }`}>
      <div className="flex items-center gap-2.5">
        {isError ? (
          <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
        ) : (
          <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
        )}
        <span>{message}</span>
      </div>
      {handleClose && (
        <button onClick={handleClose} className="text-slate-400 hover:text-white p-0.5 rounded">
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}
