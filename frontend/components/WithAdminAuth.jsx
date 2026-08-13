"use client";

import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "../providers/AuthProvider";
import { ShieldAlert } from "lucide-react";

export function AdminGuard({ children, requiredPermission = "workspace.manage" }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, role, loading, authenticated, hasAnyPermission } = useAuth();

  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#090D16] text-white">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          <span className="text-xs text-slate-400 font-medium font-mono">Verifying Access Permissions...</span>
        </div>
      </div>
    );
  }

  if (!authenticated) {
    router.replace("/login");
    return null;
  }

  const reqPerms = Array.isArray(requiredPermission) ? requiredPermission : [requiredPermission];
  const isAllowed = hasAnyPermission(reqPerms);

  if (!isAllowed) {
    const displayRole = role?.name || user?.role || "Developer";
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center bg-[#090D16] p-6 text-center text-white">
        <div className="max-w-md w-full rounded-2xl border border-rose-500/20 bg-rose-950/20 p-8 backdrop-blur-xl">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <ShieldAlert className="h-7 w-7" />
          </div>
          <h2 className="mb-2 text-xl font-bold tracking-tight text-white">403 - Access Denied</h2>
          <p className="mb-4 text-xs leading-relaxed text-slate-400">
            Your assigned role (<span className="text-indigo-300 font-semibold">{displayRole}</span>) does not have permission to access <code className="font-mono text-indigo-300">{pathname}</code>.
          </p>
          <div className="mb-6 rounded-lg bg-black/40 border border-white/10 p-3 text-left">
            <span className="text-[10px] uppercase tracking-wider text-slate-400 block mb-1 font-bold">Required Permissions:</span>
            <span className="font-mono text-xs text-rose-300">{reqPerms.filter((p) => p !== "*").join(", ") || "Administrative Access"}</span>
          </div>
          <button
            onClick={() => router.push("/dashboard")}
            className="w-full rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-indigo-500 transition shadow-lg shadow-indigo-600/30"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return children;
}

export default function WithAdminAuth(ComponentOrProps, defaultPerm = "workspace.manage") {
  if (typeof ComponentOrProps === "function" || (typeof ComponentOrProps === "object" && ComponentOrProps.$$typeof)) {
    const Component = ComponentOrProps;
    return function WrappedComponent(props) {
      return (
        <AdminGuard requiredPermission={defaultPerm}>
          <Component {...props} />
        </AdminGuard>
      );
    };
  }

  const { children, requiredPermission = defaultPerm } = ComponentOrProps || {};
  return <AdminGuard requiredPermission={requiredPermission}>{children}</AdminGuard>;
}
