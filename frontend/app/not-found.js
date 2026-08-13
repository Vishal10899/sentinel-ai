"use client";

import Link from "next/link";
import { AlertCircle, ArrowLeft, Home } from "lucide-react";
import { AppShell } from "../components/shell";

export default function NotFound() {
  return (
    <AppShell>
      <div className="flex flex-col items-center justify-center min-h-[70vh] text-center space-y-4">
        <div className="rounded-full bg-rose-500/10 p-4 border border-rose-500/20 text-rose-400">
          <AlertCircle className="h-10 w-10" />
        </div>
        <h1 className="text-3xl font-extrabold text-white">404 — Page Not Found</h1>
        <p className="text-xs text-slate-400 max-w-md">
          The requested page or enterprise control plane endpoint does not exist or has been moved.
        </p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition shadow-lg"
        >
          <Home className="h-4 w-4" /> Return to Dashboard
        </Link>
      </div>
    </AppShell>
  );
}
