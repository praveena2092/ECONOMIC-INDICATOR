import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, setUnauthorizedHandler, tokenStore } from "../api/client";

interface AuthState {
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}
const Ctx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => tokenStore.get());

  const logout = useCallback(() => { tokenStore.clear(); setToken(null); }, []);
  useEffect(() => { setUnauthorizedHandler(logout); }, [logout]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await api<{ access_token: string }>(
      "/api/v1/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }, { auth: false });
    tokenStore.set(res.access_token);
    setToken(res.access_token);
  }, []);

  const value = useMemo(() => ({ isAuthenticated: !!token, login, logout }), [token, login, logout]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used inside AuthProvider");
  return v;
}
