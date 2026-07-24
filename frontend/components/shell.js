"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, BookOpen, Boxes, BrainCircuit, Cable, ChartNoAxesCombined, ChevronRight, CircleDollarSign, Command, HeartPulse, LayoutDashboard, Menu, Settings, X } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../providers/AuthProvider";

const navigation = [
  ["Dashboard", "/dashboard", LayoutDashboard], ["Playground", "/playground", BrainCircuit], ["Providers", "/providers", Cable], ["Models", "/models", Boxes], ["Analytics", "/analytics", ChartNoAxesCombined], ["Health", "/health", HeartPulse], ["API Playground", "/api-playground", Command], ["Settings", "/settings", Settings], ["Documentation", "/documentation", BookOpen],
];

export function AppShell({ title, subtitle, children }) {
  const path = usePathname();
const [open, setOpen] = useState(false);

const router = useRouter();
const { user, logout } = useAuth();

const handleLogout = () => {
  if (!window.confirm("Log out of Sentinel AI?")) return;
  logout();
  router.replace("/login");
};
  const sidebar = <aside className="flex h-full w-72 flex-col border-r border-white/[.07] bg-[#0b0f18]/95 p-5 backdrop-blur-xl"><div className="mb-10 flex items-center justify-between"><Link href="/" className="flex items-center gap-3"><div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-indigo-400 to-violet-600 shadow-lg shadow-indigo-500/30"><Activity className="h-5 w-5" /></div><span className="font-semibold tracking-tight">Sentinel AI</span></Link><button className="lg:hidden" onClick={() => setOpen(false)}><X className="h-5 w-5" /></button></div><nav className="space-y-1">{navigation.map(([name, href, Icon]) => <Link onClick={() => setOpen(false)} key={href} href={href} className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${path === href ? "bg-indigo-500/15 text-indigo-200 ring-1 ring-indigo-400/15" : "text-slate-400 hover:bg-white/[.045] hover:text-slate-100"}`}><Icon className="h-4 w-4" />{name}</Link>)}</nav><div className="mt-auto surface p-4"><div className="flex items-center gap-2 text-sm font-medium"><HeartPulse className="h-4 w-4 text-emerald-300" />System operational</div><p className="mt-1 text-xs text-slate-500">Model registry is live.</p></div></aside>;
  return <div className="min-h-screen bg-[radial-gradient(circle_at_top_right,_rgba(99,102,241,.14),transparent_28rem)]"><div className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:block">{sidebar}</div>{open && <div className="fixed inset-0 z-50 flex lg:hidden"><div className="w-72">{sidebar}</div><button className="flex-1 bg-black/60" onClick={() => setOpen(false)} /></div>}<main className="lg:ml-72"><header className="flex items-center justify-between border-b border-white/[.07] px-5 py-4 sm:px-8"><div className="flex items-center gap-3"><button className="lg:hidden" onClick={() => setOpen(true)}><Menu className="h-5 w-5" /></button><div><h1 className="text-lg font-semibold">{title}</h1><p className="hidden text-xs text-slate-500 sm:block">{subtitle}</p></div></div><div className="flex items-center gap-3">
  <div className="hidden rounded-lg border border-white/10 bg-white/[.03] px-3 py-1.5 text-xs text-slate-400 sm:block">
    Production workspace
  </div>

  <div className="hidden sm:block text-right">
    <p className="text-sm font-medium">
  {user?.full_name || user?.name || user?.username || "User"}
</p>
  </div>

  <div className="grid h-8 w-8 place-items-center rounded-full bg-gradient-to-br from-cyan-300 to-indigo-500 text-xs font-bold text-slate-950">
    {(user?.name || "U").charAt(0).toUpperCase()}
  </div>

  <button
    onClick={handleLogout}
className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-indigo-700"  >
    Logout
  </button>
</div></header><div className="mx-auto max-w-7xl p-5 sm:p-8">{children}</div></main></div>;
}

export function PageTitle({ eyebrow, title, copy, action }) { return <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="eyebrow">{eyebrow}</p><h2 className="mt-2 text-3xl font-semibold tracking-tight">{title}</h2>{copy && <p className="mt-2 max-w-2xl text-sm text-slate-400">{copy}</p>}</div>{action}</div>; }
