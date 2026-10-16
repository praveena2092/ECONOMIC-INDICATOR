export const API_BASE_URL: string = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
export const DASHBOARD_REFRESH_MS = 5 * 60 * 1000;
export const TICKER_POLL_FALLBACK_MS = 60 * 1000;
