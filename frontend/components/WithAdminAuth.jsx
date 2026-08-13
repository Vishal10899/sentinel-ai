"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../providers/AuthProvider";
import { Toast } from "./ui";

export function AdminGuard({ children }) {
  const router = useRouter();
  const { user, role, loading, authenticated } = useAuth();
  const [toastMessage, setToastMessage] = useState("");
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    if (!loading) {
      const rawRole = (user?.role || role?.name || role?.id || "").toString().toUpperCase();
      const isAdmin = user?.role === "ADMIN" || rawRole === "ADMIN" || rawRole.includes("ADMIN") || rawRole.includes("SUPER");

      if (!authenticated || !isAdmin) {
        setToastMessage("Access Restricted: Admin privileges required");

        if (typeof window !== "undefined") {
          sessionStorage.setItem("sentinel_toast", "Access Restricted: Admin privileges required");
        }

        router.replace("/dashboard");
      } else {
        setAuthorized(true);
      }
    }
  }, [loading, authenticated, user, role, router]);

  if (loading || !authorized) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#090D16] text-white">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          <span className="text-xs text-slate-400 font-medium font-mono">Verifying Admin Privileges...</span>
        </div>
        {toastMessage && <Toast message={toastMessage} clear={() => setToastMessage("")} />}
      </div>
    );
  }

  return (
    <>
      {children}
      {toastMessage && <Toast message={toastMessage} clear={() => setToastMessage("")} />}
    </>
  );
}

export default function WithAdminAuth(ComponentOrProps) {
  if (typeof ComponentOrProps === "function" || (typeof ComponentOrProps === "object" && ComponentOrProps.$$typeof)) {
    const Component = ComponentOrProps;
    return function WrappedComponent(props) {
      return (
        <AdminGuard>
          <Component {...props} />
        </AdminGuard>
      );
    };
  }

  const { children } = ComponentOrProps || {};
  return <AdminGuard>{children}</AdminGuard>;
}
