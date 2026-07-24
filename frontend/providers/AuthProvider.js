"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  clearSession,
  getUser,
  hasSession,
  saveSession,
} from "../utils/storage";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (hasSession()) {
      setUser(getUser());
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    const expire = () => {
      clearSession();
      setUser(null);
      router.replace("/login?reason=expired");
    };
    window.addEventListener("sentinel:session-expired", expire);
    return () => window.removeEventListener("sentinel:session-expired", expire);
  }, [router]);

  const login = (session) => {
    saveSession(session);
    setUser(session.user);
  };

  const logout = () => {
    clearSession();
    setUser(null);
  };

  const value = useMemo(
    () => ({
      user,
      loading,
      authenticated: !!user,
      login,
      logout,
    }),
    [user, loading]
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
