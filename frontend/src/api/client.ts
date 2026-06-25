import { currentToken } from "@/store/auth";

export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8080";
export const WS_BASE = import.meta.env.VITE_WS_BASE ?? "ws://localhost:8080";

export async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const token = currentToken();
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!res.ok) {
    let message = `请求失败 (${res.status})`;
    try {
      const body = await res.json();
      if (body?.message) message = body.message;
    } catch {
      /* ignore */
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}
