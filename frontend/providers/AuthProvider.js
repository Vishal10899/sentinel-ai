"use client";

import { createContext, useContext, useEffect, useMemo, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  clearSession,
  getUser,
  hasSession,
  saveSession,
} from "../utils/storage";
import { api, clearApiCache } from "../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [authContext, setAuthContext] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshContext = async () => {
    if (!hasSession()) {
      setUser(null);
      setAuthContext(null);
      setLoading(false);
      return;
    }
    try {
      const data = await api.me();
      if (data && data.user) {
        setUser(data.user);
        setAuthContext(data);
      } else {
        const cachedUser = getUser();
        setUser(cachedUser);
      }
    } catch (e) {
      console.warn("Failed to fetch authorization context from server:", e);
      const cachedUser = getUser();
      setUser(cachedUser);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshContext();
  }, []);

  useEffect(() => {
    const expire = () => {
      clearSession();
      clearApiCache();
      setUser(null);
      setAuthContext(null);
      router.replace("/login?reason=expired");
    };
    window.addEventListener("sentinel:session-expired", expire);
    return () => window.removeEventListener("sentinel:session-expired", expire);
  }, [router]);

  const login = async (session) => {
    clearApiCache();
    saveSession(session);
    if (session?.access_token) {
      try {
        const data = await api.me();
        if (data && data.user) {
          setUser(data.user);
          setAuthContext(data);
          return;
        }
      } catch (e) {
        console.warn("Could not fetch immediate /auth/me on login:", e);
      }
    }
    if (session?.user) {
      setUser(session.user);
    }
    if (session?.permissions) {
      setAuthContext(session);
    } else {
      await refreshContext();
    }
  };

  const logout = () => {
    clearSession();
    clearApiCache();
    setUser(null);
    setAuthContext(null);
    router.replace("/login");
  };

  const permissions = useMemo(() => authContext?.permissions || [], [authContext]);

  const hasPermission = useCallback(
    (perm) => {
      if (!perm) return true;
      if (permissions.includes("*")) return true;
      return permissions.includes(perm);
    },
    [permissions]
  );

  const hasAnyPermission = useCallback(
    (permsList) => {
      if (!permsList || permsList.length === 0) return true;
      if (permissions.includes("*")) return true;
      return permsList.some((p) => p === "*" || permissions.includes(p));
    },
    [permissions]
  );

  const value = useMemo(
    () => ({
      user: authContext?.user || user,
      organization: authContext?.organization || null,
      workspace: authContext?.workspace || null,
      role: authContext?.role || null,
      permissions,
      loading,
      authenticated: !!(authContext?.user || user),
      login,
      logout,
      refreshContext,
      hasPermission,
      hasAnyPermission,
    }),
    [user, authContext, permissions, loading, hasPermission, hasAnyPermission]
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
