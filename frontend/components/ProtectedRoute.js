"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "../providers/AuthProvider";

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

export default function ProtectedRoute({ children, requiredPermission }) {
  const { authenticated, loading, permissions } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !authenticated) {
      router.replace("/login");
    }
  }, [loading, authenticated, router]);

  if (loading) return null;
  if (!authenticated) return null;

  const reqPerms = requiredPermission
    ? [requiredPermission, "*"]
    : ROUTE_PERMISSIONS[pathname];

  if (reqPerms) {
    const userPerms = permissions || [];
    const hasPerm =
      userPerms.includes("*") ||
      reqPerms.some((p) => userPerms.includes(p));

    if (!hasPerm) {
      return (
        <div className="flex h-screen w-full flex-col items-center justify-center bg-[#090D16] p-6 text-center text-white">
          <div className="max-w-md rounded-2xl border border-rose-500/20 bg-rose-950/20 p-8 backdrop-blur-xl">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-500/10 text-rose-400 border border-rose-500/30">
              <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="mb-2 text-xl font-bold tracking-tight text-white">403 - Access Denied</h2>
            <p className="mb-6 text-xs leading-relaxed text-slate-400">
              Your assigned role does not have permission to access the route <code className="font-mono text-indigo-300">{pathname}</code>.
            </p>
            <button
              onClick={() => router.push("/dashboard")}
              className="w-full rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-indigo-500 transition"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      );
    }
  }

  return children;
}