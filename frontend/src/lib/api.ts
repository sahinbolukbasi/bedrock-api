import { setSessionCookie, getSessionCookie, removeSessionCookie, publishLiveSyncEvent } from "./sync-engine";

export const API_BASE = "";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  const lsToken = localStorage.getItem("bedrock_gateway_token");
  if (lsToken) return lsToken;
  const cookieToken = getSessionCookie("bg_auth_token");
  if (cookieToken) {
    localStorage.setItem("bedrock_gateway_token", cookieToken);
    return cookieToken;
  }
  return null;
}

export function setAuthToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("bedrock_gateway_token", token);
    setSessionCookie("bg_auth_token", token);
    publishLiveSyncEvent("AUTH_UPDATED", { token });
  }
}

export function clearAuthToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("bedrock_gateway_token");
    localStorage.removeItem("bedrock_gateway_user");
    localStorage.removeItem("bedrock_gateway_balance");
    removeSessionCookie("bg_auth_token");
    removeSessionCookie("bg_user_balance");
    publishLiveSyncEvent("AUTH_UPDATED", { token: null });
  }
}

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = errorData?.error?.message || errorData?.detail || `API Error: ${response.status}`;
    throw new Error(message);
  }

  return response.json();
}

