"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { api, getTokens, saveTokens, SESSION_EXPIRED_EVENT } from "./api";
import type { Role, User } from "./types";

type AuthStatus = "loading" | "signed-in" | "signed-out";

type AuthContextValue = {
  user: User | null;
  status: AuthStatus;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (...roles: Role[]) => boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

/** Remembers who is logged in, so every screen can ask `useAuth()`. */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  // On first load: if tokens are saved from an earlier visit, find out who they belong to.
  useEffect(() => {
    async function restoreSession(): Promise<User | null> {
      if (!getTokens()) return null;
      try {
        return await api<User>("/api/auth/me/");
      } catch {
        saveTokens(null);
        return null;
      }
    }
    restoreSession().then((me) => {
      setUser(me);
      setStatus(me ? "signed-in" : "signed-out");
    });
  }, []);

  // When the API helper finds the session has expired, go to the login page with a message.
  useEffect(() => {
    function onExpired() {
      setUser(null);
      setStatus("signed-out");
      router.replace("/login?expired=1");
    }
    window.addEventListener(SESSION_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, onExpired);
  }, [router]);

  const login = useCallback(async (username: string, password: string) => {
    saveTokens(null); // never send an old token with a login attempt
    const tokens = await api<{ access: string; refresh: string }>("/api/auth/login/", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    saveTokens(tokens);
    setUser(await api<User>("/api/auth/me/"));
    setStatus("signed-in");
  }, []);

  const logout = useCallback(async () => {
    const tokens = getTokens();
    if (tokens) {
      // Tell Django to blacklist the refresh token. If that fails, we still log out locally.
      await api("/api/auth/logout/", { method: "POST", body: JSON.stringify({ refresh: tokens.refresh }) }).catch(
        () => undefined,
      );
    }
    saveTokens(null);
    setUser(null);
    setStatus("signed-out");
    router.replace("/login");
  }, [router]);

  const hasRole = useCallback((...roles: Role[]) => user !== null && roles.includes(user.role), [user]);

  return <AuthContext.Provider value={{ user, status, login, logout, hasRole }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside <AuthProvider>");
  return value;
}
