import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api/client";
import type { DashboardData } from "../api/types";
import { DASHBOARD_REFRESH_MS } from "../config";

export interface DashboardState {
  data: DashboardData | null;
  loading: boolean;
  error: ApiError | null;     // set when the latest attempt failed
  reload: () => void;
}

/** Loads the dashboard, refreshes periodically, and keeps the last good payload if a refresh fails. */
export function useDashboard(): DashboardState {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const load = useCallback(async () => {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    try {
      const res = await api<DashboardData>("/api/v1/dashboard", {}, { signal: ctrl.signal });
      setData(res);
      setError(null);
    } catch (e) {
      if ((e as Error).name === "AbortError") return;
      setError(e instanceof ApiError ? e : new ApiError(0, "unknown", "Unexpected error"));
    } finally {
      if (abortRef.current === ctrl) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    const id = setInterval(() => void load(), DASHBOARD_REFRESH_MS);
    return () => { clearInterval(id); abortRef.current?.abort(); };
  }, [load]);

  return { data, loading, error, reload: () => { setLoading(true); void load(); } };
}
