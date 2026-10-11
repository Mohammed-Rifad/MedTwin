const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const TOKENS_KEY = "medtwin.tokens";

export const SESSION_EXPIRED_EVENT = "medtwin:session-expired";

type Tokens = { access: string; refresh: string };

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, data: unknown) {
    super(messageFrom(data) ?? `Request failed (${status})`);
    this.status = status;
    this.data = data;
  }
}

// Django sends errors as {"detail": "..."} or {"field": ["..."]}. Pick a readable message.
function messageFrom(data: unknown): string | undefined {
  if (!data || typeof data !== "object") return undefined;
  if ("detail" in data) return String((data as { detail: unknown }).detail);
  const first = Object.values(data)[0];
  return Array.isArray(first) ? String(first[0]) : undefined;
}

export function getTokens(): Tokens | null {
  if (typeof window === "undefined") return null;
  const saved = localStorage.getItem(TOKENS_KEY);
  return saved ? (JSON.parse(saved) as Tokens) : null;
}

export function saveTokens(tokens: Tokens | null) {
  if (tokens) localStorage.setItem(TOKENS_KEY, JSON.stringify(tokens));
  else localStorage.removeItem(TOKENS_KEY);
}

// If several requests find the token expired at the same moment, they share ONE refresh.
// (Refresh tokens are single-use, so two refreshes with the same token would log the user out.)
let refreshing: Promise<boolean> | null = null;

function refreshAccessToken(): Promise<boolean> {
  const tokens = getTokens();
  if (!tokens) return Promise.resolve(false);
  refreshing ??= (async () => {
    const response = await fetch(`${API_URL}/api/auth/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: tokens.refresh }),
    });
    if (!response.ok) return false;
    const data = await response.json();
    saveTokens({ access: data.access, refresh: data.refresh ?? tokens.refresh });
    return true;
  })().finally(() => {
    refreshing = null;
  });
  return refreshing;
}

/**
 * Call the Django API. Adds the login token, renews it quietly when it expires,
 * and throws an ApiError with a readable message when Django reports a problem.
 */
export async function api<T>(path: string, options: RequestInit = {}, canRetry = true): Promise<T> {
  const tokens = getTokens();
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (tokens) headers.set("Authorization", `Bearer ${tokens.access}`);

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (response.status === 401 && tokens) {
    if (canRetry && (await refreshAccessToken())) {
      return api<T>(path, options, false); // try once more with the new token
    }
    saveTokens(null);
    window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
  }

  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, data);
  return data as T;
}
