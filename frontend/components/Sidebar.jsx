"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  BookOpen,
  Boxes,
  BrainCircuit,
  Building2,
  Cable,
  ChartNoAxesCombined,
  Cpu,
  FileText,
  FlaskConical,
  HeartPulse,
  Key,
  LayoutDashboard,
  Lock,
  LogOut,
  ShieldAlert,
  ShieldCheck,
  Sliders,
  Sparkles,
  Users,
  X,
  Zap,
} from "lucide-react";
import { useAuth } from "../providers/AuthProvider";
import { ROUTE_PERMISSIONS } from "./ProtectedRoute";


const navigationGroups = [
  {
    group: "OVERVIEW",
    items: [
      { label: "Dashboard", route: "/dashboard", icon: LayoutDashboard },
      { label: "FinOps & Analytics", route: "/analytics", icon: ChartNoAxesCombined },
    ],
  },
  {
    group: "GATEWAY & RUNTIME",
    items: [
      { label: "Developer Gateway & Playground", route: "/playground", icon: BrainCircuit },
      { label: "Provider Integrations", route: "/providers", icon: Cable },
      { label: "Model Catalog", route: "/models", icon: Boxes },
    ],
  },
  {
    group: "ORCHESTRATION & RESILIENCE",
    items: [
      { label: "Adaptive Routing", route: "/routing-center", icon: Cpu },
      { label: "Circuit Breakers & Failover", route: "/circuit-breakers", icon: HeartPulse },
      { label: "MCP Governance", route: "/mcp-governance", icon: ShieldCheck },
      { label: "Semantic Cache", route: "/cache", icon: Zap },
    ],
  },
  {
    group: "SECURITY & COMPLIANCE",
    items: [
      { label: "Inline DLP & PII Redaction", route: "/dlp", icon: ShieldAlert },
      { label: "AI Guardrails", route: "/guardrails", icon: Lock },
      { label: "Virtual API Keys", route: "/virtual-keys", icon: Key },
      { label: "Governance Policies", route: "/policies", icon: Sliders },
      { label: "Policy Simulator", route: "/policy-simulator", icon: FlaskConical },
    ],
  },
  {
    group: "IDENTITY & AUDIT",
    items: [
      { label: "Organizations & Workspaces", route: "/organizations", icon: Building2 },
      { label: "Roles & RBAC Matrix", route: "/roles", icon: Users },
      { label: "Audit Logs", route: "/audit", icon: FileText },
    ],
  },
  {
    group: "OPERATIONS",
    items: [
      { label: "Agentic Tracing", route: "/agentic-tracing", icon: Sparkles },
      { label: "Observability", route: "/observability", icon: Activity },
      { label: "Platform Settings", route: "/settings", icon: Sliders },
      { label: "Documentation", route: "/documentation", icon: BookOpen },
    ],
  },
];

export default function Sidebar({ mobileOpen = false, setMobileOpen = () => {} }) {
  const path = usePathname();
  const { user, role, permissions, logout, hasAnyPermission } = useAuth();

  const displayName = user?.name || user?.email?.split("@")[0] || "User";
  const displayRole = role?.name || user?.role || "Developer";
  const avatarLetter = (displayName[0] || "U").toUpperCase();

  // Filter navigation groups based on server-authoritative effective permissions
  const visibleGroups = navigationGroups
    .map((group) => {
      const visibleItems = group.items.filter((item) => {
        const reqPerms = ROUTE_PERMISSIONS[item.route];
        if (!reqPerms) return true; // public / doc routes
        return hasAnyPermission(reqPerms);
      });
      return { ...group, items: visibleItems };
    })
    .filter((group) => group.items.length > 0);

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

      {/* Permission-aware Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-6">
        {visibleGroups.map((group) => (
          <div key={group.group} className="space-y-1">
            <span className="px-2.5 text-[9px] font-bold uppercase tracking-widest text-[var(--text-muted)] block mb-1">
              {group.group}
            </span>
            {group.items.map(({ label, route, icon: Icon }) => {
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
        ))}
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
