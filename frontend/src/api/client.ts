import { API_BASE_URL } from "../config";

const TOKEN_KEY = "eid.token";
export const tokenStore = {
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (t: string) => sessionStorage.setItem(TOKEN_KEY, t),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
};

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public requestId?: string) {
    super(message);
  }
}

let onUnauthorized: () => void = () => {};
export const setUnauthorizedHandler = (fn: () => void) => { onUnauthorized = fn; };

export async function parseError(res: Response): Promise<ApiError> {
  try {
    const body = await res.json();
    const e = body?.error;
    if (e) return new ApiError(res.status, e.code, e.message, e.request_id);
  } catch { /* fall through */ }
  return new ApiError(res.status, "http_error", `Request failed (${res.status})`);
}

export async function api<T>(path: string, init: RequestInit = {}, opts: { auth?: boolean; signal?: AbortSignal } = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body) headers.set("Content-Type", "application/json");
  const token = tokenStore.get();
  if (opts.auth !== false && token) headers.set("Authorization", `Bearer ${token}`);

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { ...init, headers, signal: opts.signal });
  } catch (e) {
    if ((e as Error).name === "AbortError") throw e;
    throw new ApiError(0, "network_error", "Cannot reach the server. Check your connection and try again.");
  }
  if (!res.ok) {
    const err = await parseError(res);
    if (res.status === 401 && opts.auth !== false) onUnauthorized();
    throw err;
  }
  return res.json() as Promise<T>;
}
