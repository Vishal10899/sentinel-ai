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
  ChevronDown,
  ChevronRight,
  CircleDollarSign,
  Command,
  Cpu,
  FileText,
  FlaskConical,
  HeartPulse,
  HelpCircle,
  Key,
  LayoutDashboard,
  LogOut,
  Menu,
  Bell,
  Search,
  Settings,
  ShieldAlert,
  Sliders,
  Sparkles,
  User,
  Users,
  X,
  Zap,
  Moon,
  Sun,
  Check,
  ShieldCheck,
  Lock
} from "lucide-react";
import { useState, useEffect } from "react";
import { useAuth } from "../providers/AuthProvider";
import { useTheme } from "../providers/ThemeProvider";
import ProtectedRoute from "./ProtectedRoute";

import Sidebar from "./Sidebar";

const groupedNavigation = [
  {
    group: "OVERVIEW",
    items: [
      ["Dashboard", "/dashboard", LayoutDashboard],
      ["FinOps & Analytics", "/analytics", ChartNoAxesCombined],
    ],
  },
  {
    group: "GATEWAY & RUNTIME",
    items: [
      ["Developer Gateway & Playground", "/playground", BrainCircuit],
      ["Provider Integrations", "/providers", Cable],
      ["Model Catalog", "/models", Boxes],
    ],
  },
  {
    group: "ORCHESTRATION & RESILIENCE",
    items: [
      ["Adaptive Routing", "/routing-center", Cpu],
      ["Circuit Breakers & Failover", "/circuit-breakers", HeartPulse],
      ["MCP Governance", "/mcp-governance", ShieldCheck],
      ["Semantic Cache", "/cache", Zap],
    ],
  },
  {
    group: "SECURITY & COMPLIANCE",
    items: [
      ["Inline DLP & PII Redaction", "/dlp", ShieldAlert],
      ["AI Guardrails", "/guardrails", Lock],
      ["Virtual API Keys", "/virtual-keys", Key],
      ["Governance Policies", "/policies", Sliders],
      ["Policy Simulator", "/policy-simulator", FlaskConical],
    ],
  },
  {
    group: "IDENTITY & AUDIT",
    items: [
      ["Organizations & Workspaces", "/organizations", Building2],
      ["Roles & RBAC Matrix", "/roles", Users],
      ["Audit Logs", "/audit", FileText],
    ],
  },
  {
    group: "OPERATIONS",
    items: [
      ["Agentic Tracing", "/agentic-tracing", Sparkles],
      ["Observability", "/observability", Activity],
      ["Platform Settings", "/settings", Settings],
      ["Documentation", "/documentation", BookOpen],
    ],
  },
];


const ROUTE_PERMISSIONS = {
  "/dashboard": ["conversation.read", "chat.read", "analytics.read", "*"],
  "/analytics": ["analytics.read", "view_analytics", "*"],
  "/playground": ["chat.read", "chat.write", "*"],
  "/providers": ["provider.manage", "manage_providers", "*"],
  "/models": ["view_models", "model.manage", "*"],
  "/routing-center": ["model.manage", "provider.manage", "*"],
  "/circuit-breakers": ["provider.manage", "manage_providers", "*"],
  "/mcp-governance": ["policy.manage", "guardrails.manage", "*"],
  "/cache": ["cache.manage", "*"],
  "/dlp": ["guardrails.manage", "policy.manage", "*"],
  "/guardrails": ["guardrails.manage", "*"],
  "/virtual-keys": ["apikey.manage", "create_api_keys", "*"],
  "/policies": ["policy.manage", "manage_policies", "*"],
  "/policy-simulator": ["policy.manage", "manage_policies", "*"],
  "/organizations": ["workspace.manage", "manage_workspaces", "*"],
  "/roles": ["users.manage", "rbac.manage", "*"],
  "/audit": ["audit.read", "audit.export", "*"],
  "/agentic-tracing": ["analytics.read", "audit.read", "*"],
  "/observability": ["analytics.read", "*"],
  "/settings": ["settings.manage", "manage_workspaces", "*"],
  "/documentation": null,
};

export function AppShell({ title, subtitle, children }) {
  const path = usePathname();
  const router = useRouter();
  const { user, role, permissions, logout, loading, authenticated } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [activeWorkspace, setActiveWorkspace] = useState("Default Workspace");
  const [isWorkspaceMenuOpen, setIsWorkspaceMenuOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const { theme, toggleTheme } = useTheme();
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);

  const unauthenticatedAllowedRoutes = ["/", "/login", "/register", "/forgot-password", "/documentation", "/health"];
  const rawAuthRoutes = ["/", "/login", "/register", "/forgot-password"];

  const isRawAuthRoute = rawAuthRoutes.includes(path);
  const isUnauthenticatedAllowed = unauthenticatedAllowedRoutes.includes(path);

  const userPermissions = permissions || [];
  const displayRole = role?.name || user?.role || "Member";

  // Filter navigation groups based on effective user permissions
  const visibleGroups = groupedNavigation
    .map((group) => {
      const visibleItems = group.items.filter(([, route]) => {
        const reqPerms = ROUTE_PERMISSIONS[route];
        if (!reqPerms) return true;
        if (!userPermissions || !Array.isArray(userPermissions)) return false;
        if (userPermissions.includes("*")) return true;
        return reqPerms.some((p) => userPermissions.includes(p));
      });
      return { ...group, items: visibleItems };
    })
    .filter((group) => group.items.length > 0);

  // Set active workspace from user object if available
  useEffect(() => {
    if (user?.workspaces?.length > 0) {
      setActiveWorkspace(user.workspaces[0].name || user.workspaces[0]);
    } else if (user?.workspace_id) {
      setActiveWorkspace(user.workspace_id);
    }
  }, [user]);

  // Auth Guard: Redirect unauthenticated users immediately on protected routes
  useEffect(() => {
    if (!isUnauthenticatedAllowed && !loading && !authenticated) {
      router.replace("/login");
    }
  }, [isUnauthenticatedAllowed, loading, authenticated, router]);

  // Keyboard shortcut ⌘K listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
      }
      if (e.key === "Escape") {
        setIsSearchOpen(false);
        setIsWorkspaceMenuOpen(false);
        setIsProfileMenuOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Raw auth routes (login, register, landing) render immediately without shell layout
  if (isRawAuthRoute) {
    return <main className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans">{children}</main>;
  }

  // Loading state: Show clean loading screen before auth verification
  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#090D16] text-white">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          <span className="text-xs text-slate-400 font-medium font-mono">Verifying Sentinel Session...</span>
        </div>
      </div>
    );
  }

  // If unauthenticated on protected route, do NOT render shell layout or sidebar
  if (!authenticated && !isUnauthenticatedAllowed) {
    return null;
  }

  const workspaces = user?.workspaces?.map((w) => typeof w === "string" ? w : w.name) || [
    "Default Workspace",
    "Staging Gateway",
    "Security Sandbox"
  ];

  const searchResults = searchQuery.trim()
    ? groupedNavigation.flatMap((g) => g.items).filter(([label]) => label.toLowerCase().includes(searchQuery.toLowerCase()))
    : [];

  const displayName = user?.name || user?.email?.split("@")[0] || "User";
  const avatarLetter = (displayName[0] || "U").toUpperCase();

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans antialiased select-none">
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar Navigation */}
      <Sidebar mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} />

      {/* Main Content Workspace */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Header */}
        <header className="flex h-14 items-center justify-between border-b border-[var(--border-color)] bg-[var(--header-bg)] px-4 md:px-6 backdrop-blur-md shrink-0">
          <div className="flex items-center gap-3">
            <button className="lg:hidden text-[var(--text-secondary)] hover:text-[var(--text-primary)]" onClick={() => setMobileOpen(true)}>
              <Menu className="h-4 w-4" />
            </button>

            {/* Workspace Selector Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsWorkspaceMenuOpen(!isWorkspaceMenuOpen)}
                className="flex items-center gap-2 text-xs font-semibold text-[var(--text-primary)] bg-[var(--bg-surface)] hover:border-[var(--border-hover)] border border-[var(--border-color)] px-3 py-1.5 rounded-lg transition"
              >
                <Building2 className="h-3.5 w-3.5 text-indigo-400" />
                <span>{activeWorkspace}</span>
                <ChevronDown className="h-3 w-3 text-[var(--text-secondary)]" />
              </button>

              {isWorkspaceMenuOpen && (
                <div className="absolute left-0 mt-2 w-56 rounded-xl border border-[var(--border-color)] bg-[var(--bg-surface)] p-1.5 shadow-2xl z-50">
                  <div className="px-2 py-1 text-[9px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                    Select Active Workspace
                  </div>
                  {workspaces.map((ws) => (
                    <button
                      key={ws}
                      onClick={() => {
                        setActiveWorkspace(ws);
                        setIsWorkspaceMenuOpen(false);
                      }}
                      className="w-full flex items-center justify-between rounded-lg px-2.5 py-1.5 text-xs text-left text-[var(--text-secondary)] hover:bg-white/[0.06] hover:text-[var(--text-primary)] transition"
                    >
                      <span>{ws}</span>
                      {activeWorkspace === ws && <Check className="h-3.5 w-3.5 text-indigo-400" />}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Global Search Bar Trigger (⌘K) */}
            <button
              onClick={() => setIsSearchOpen(true)}
              className="hidden md:flex items-center gap-2 bg-[var(--bg-surface)] border border-[var(--border-color)] hover:border-[var(--border-hover)] px-3 py-1 rounded-lg text-xs text-[var(--text-secondary)] min-w-[220px] transition"
            >
              <Search className="h-3.5 w-3.5 text-[var(--text-secondary)]" />
              <span>Search control plane...</span>
              <kbd className="ml-auto font-mono text-[9px] bg-white/10 border border-[var(--border-color)] px-1.5 py-0.5 rounded text-[var(--text-secondary)]">⌘K</kbd>
            </button>
          </div>

          {/* Right Actions & Controls */}
          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-[10px] font-mono text-emerald-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>PROXY ACTIVE (0.8ms P95)</span>
            </div>

            <button
              onClick={toggleTheme}
              title="Toggle Theme"
              className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.06] transition"
            >
              {theme === "dark" ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-indigo-400" />}
            </button>

            <Link href="/observability" className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.06] transition" title="Notifications">
              <Bell className="h-4 w-4" />
            </Link>

            <Link href="/documentation" className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/[0.06] transition" title="Documentation">
              <BookOpen className="h-4 w-4" />
            </Link>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 bg-[var(--bg-primary)]">{children}</main>
      </div>

      {/* ⌘K Command Search Palette Modal */}
      {isSearchOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-xl rounded-2xl border border-[var(--border-color)] bg-[var(--bg-surface)] p-4 shadow-2xl space-y-3">
            <div className="flex items-center gap-3 border-b border-[var(--border-color)] pb-3">
              <Search className="h-4 w-4 text-indigo-400" />
              <input
                type="text"
                autoFocus
                placeholder="Search modules, API keys, guardrails..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-transparent text-sm text-[var(--text-primary)] outline-none placeholder:text-[var(--text-muted)] font-medium"
              />
              <button onClick={() => setIsSearchOpen(false)} className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-xs font-mono bg-white/10 px-2 py-0.5 rounded">
                ESC
              </button>
            </div>

            <div className="max-h-80 overflow-y-auto space-y-1">
              {searchResults.length === 0 ? (
                <p className="text-xs text-[var(--text-secondary)] p-4 text-center">
                  {searchQuery ? "No matching modules found." : "Type to search Sentinel AI control plane."}
                </p>
              ) : (
                searchResults.map(([label, route, Icon]) => (
                  <Link
                    key={route}
                    href={route}
                    onClick={() => setIsSearchOpen(false)}
                    className="flex items-center gap-3 rounded-xl p-2.5 text-xs text-[var(--text-secondary)] hover:bg-white/[0.06] hover:text-[var(--text-primary)] transition"
                  >
                    <Icon className="h-4 w-4 text-indigo-400" />
                    <span className="font-semibold">{label}</span>
                    <span className="ml-auto text-[10px] font-mono text-[var(--text-muted)]">{route}</span>
                  </Link>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function PageTitle({ title, subtitle, eyebrow, action }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border-color)] pb-4 mb-6">
      <div>
        {eyebrow && <span className="eyebrow block mb-1">{eyebrow}</span>}
        <h1 className="text-lg font-bold text-[var(--text-primary)] tracking-tight">{title}</h1>
        {subtitle && <p className="text-xs text-[var(--text-secondary)] mt-0.5">{subtitle}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
