"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  clearSession,
  getUser,
  hasSession,
  saveSession,
} from "../utils/storage";
import { api } from "../lib/api";

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
      setUser(null);
      setAuthContext(null);
      router.replace("/login?reason=expired");
    };
    window.addEventListener("sentinel:session-expired", expire);
    return () => window.removeEventListener("sentinel:session-expired", expire);
  }, [router]);

  const login = (session) => {
    saveSession(session);
    if (session.user) {
      setUser(session.user);
    }
    if (session.permissions) {
      setAuthContext(session);
    } else {
      refreshContext();
    }
  };

  const logout = () => {
    clearSession();
    setUser(null);
    setAuthContext(null);
    router.replace("/login");
  };

  const value = useMemo(
    () => ({
      user: authContext?.user || user,
      organization: authContext?.organization || null,
      workspace: authContext?.workspace || null,
      role: authContext?.role || null,
      permissions: authContext?.permissions || [],
      loading,
      authenticated: !!(authContext?.user || user),
      login,
      logout,
      refreshContext,
    }),
    [user, authContext, loading]
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
