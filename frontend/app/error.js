"use client";

import { useEffect } from "react";
import { ShieldAlert, RefreshCw } from "lucide-react";
import { AppShell } from "../components/shell";

export default function Error({ error, reset }) {
  useEffect(() => {
    console.error("Unhandled Application Error:", error);
  }, [error]);

  return (
    <AppShell>
      <div className="flex flex-col items-center justify-center min-h-[70vh] text-center space-y-4">
        <div className="rounded-full bg-rose-500/10 p-4 border border-rose-500/20 text-rose-400">
          <ShieldAlert className="h-10 w-10" />
        </div>
        <h1 className="text-3xl font-extrabold text-white">500 — Application Error</h1>
        <p className="text-xs text-slate-400 max-w-md">
          An unhandled error occurred within the Sentinel AI control plane client.
        </p>
        <button
          onClick={() => reset()}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition shadow-lg"
        >
          <RefreshCw className="h-4 w-4" /> Try Again
        </button>
      </div>
    </AppShell>
  );
}
