"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  BrainCircuit,
  Cable,
  CircleDollarSign,
  Key,
  LayoutDashboard,
  LogOut,
  ShieldAlert,
  ShieldCheck,
  Users,
  X,
} from "lucide-react";
import { useAuth } from "../providers/AuthProvider";

export default function Sidebar({ mobileOpen = false, setMobileOpen = () => {} }) {
  const path = usePathname();
  const router = useRouter();
  const { user, role, logout } = useAuth();

  // Role extraction and normalize check
  const rawRole = (user?.role || role?.name || role?.id || "").toString().toUpperCase();
  const isAdmin = user?.role === "ADMIN" || rawRole === "ADMIN" || rawRole.includes("ADMIN") || rawRole.includes("SUPER");

  // Universal Links (Visible to ALL roles)
  const universalLinks = [
    { label: "Overview", route: "/dashboard", icon: LayoutDashboard },
    { label: "Interactive Playground", route: "/playground", icon: BrainCircuit },
    { label: "Virtual API Keys", route: "/virtual-keys", icon: Key },
    { label: "Observability & Spans", route: "/traces", icon: Activity },
  ];

  // Admin-Only Links (Visible ONLY when user is ADMIN)
  const adminLinks = [
    { label: "Provider API Keys", route: "/providers", icon: Cable },
    { label: "DLP & MCP Security Policies", route: "/security", icon: ShieldAlert },
    { label: "Workspace Budget Caps", route: "/settings/budget", icon: CircleDollarSign },
    { label: "Team & Member Management", route: "/settings/team", icon: Users },
  ];

  const displayName = user?.name || user?.email?.split("@")[0] || "User";
  const displayRole = user?.role || (isAdmin ? "ADMIN" : "DEVELOPER");
  const avatarLetter = (displayName[0] || "U").toUpperCase();

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-[var(--border-color)] bg-[var(--sidebar-bg)] backdrop-blur-xl transition-transform duration-300 lg:static lg:translate-x-0 ${
        mobileOpen ? "translate-x-0" : "-translate-x-full"
      }`}
    >
      {/* Brand Header */}
      <div className="flex h-14 items-center justify-between px-4 border-b border-[var(--border-color)] shrink-0">
        <Link href="/dashboard" className="flex items-center gap-2.5 group">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600/20 border border-indigo-500/40 text-indigo-400 group-hover:scale-105 transition-transform">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold tracking-tight text-[var(--text-primary)] leading-none flex items-center gap-1">
              SENTINEL<span className="text-indigo-400">.AI</span>
            </span>
            <span className="text-[9px] font-mono text-[var(--text-muted)] tracking-wider uppercase mt-0.5">
              AI Security Gateway
            </span>
          </div>
        </Link>
        <button
          className="lg:hidden text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          onClick={() => setMobileOpen(false)}
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-6">
        {/* Universal Links Section */}
        <div className="space-y-1">
          <span className="px-2.5 text-[9px] font-bold uppercase tracking-widest text-[var(--text-muted)] block mb-1">
            CORE PLATFORM
          </span>
          {universalLinks.map(({ label, route, icon: Icon }) => {
            const active = path === route;
            return (
              <Link
                key={route}
                href={route}
                onClick={() => setMobileOpen(false)}
                className={`flex items-center justify-between rounded-lg px-2.5 py-2 text-xs font-medium transition-all ${
                  active
                    ? "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 font-semibold shadow-sm"
                    : "text-[var(--text-secondary)] hover:bg-white/[0.04] hover:text-[var(--text-primary)]"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`h-4 w-4 ${active ? "text-indigo-400" : "text-[var(--text-secondary)]"}`} />
                  <span>{label}</span>
                </div>
                {active && <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" />}
              </Link>
            );
          })}
        </div>

        {/* Admin-Only Section */}
        {isAdmin && (
          <div className="space-y-1 pt-2 border-t border-[var(--border-color)]">
            <span className="px-2.5 text-[9px] font-bold uppercase tracking-widest text-indigo-400 block mb-1 flex items-center gap-1">
              ADMINISTRATION
            </span>
            {adminLinks.map(({ label, route, icon: Icon }) => {
              const active = path === route;
              return (
                <Link
                  key={route}
                  href={route}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center justify-between rounded-lg px-2.5 py-2 text-xs font-medium transition-all ${
                    active
                      ? "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 font-semibold shadow-sm"
                      : "text-[var(--text-secondary)] hover:bg-white/[0.04] hover:text-[var(--text-primary)]"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`h-4 w-4 ${active ? "text-indigo-400" : "text-[var(--text-secondary)]"}`} />
                    <span>{label}</span>
                  </div>
                  {active && <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" />}
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {/* User Profile Footer */}
      <div className="border-t border-[var(--border-color)] p-3 bg-[var(--bg-primary)] shrink-0 space-y-2 relative">
        <div className="flex items-center justify-between p-1.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-surface)] hover:border-[var(--border-hover)] transition cursor-pointer">
          <Link href="/profile" className="flex items-center gap-2.5 overflow-hidden flex-1">
            <div className="relative shrink-0">
              <div className="h-8 w-8 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center font-bold text-indigo-300 text-xs">
                {avatarLetter}
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-emerald-500 border-2 border-[var(--bg-primary)]" />
            </div>
            <div className="truncate">
              <p className="text-xs font-semibold text-[var(--text-primary)] truncate leading-tight">{displayName}</p>
              <span className="text-[9px] text-indigo-400 font-mono tracking-tight block truncate uppercase">
                {displayRole}
              </span>
            </div>
          </Link>

          <button
            onClick={() => logout()}
            title="Sign Out"
            className="p-1.5 text-[var(--text-secondary)] hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition shrink-0 ml-1"
          >
            <LogOut className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
}
