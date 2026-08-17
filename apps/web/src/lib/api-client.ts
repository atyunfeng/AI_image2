import "server-only";
import { cookies } from "next/headers";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = (await cookies()).get("aiimage_session")?.value;
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers, cache: "no-store" });
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.json() as Promise<T>;
}

export async function safeApiFetch<T>(path: string, fallback: T): Promise<T> {
  try { return await apiFetch<T>(path); } catch { return fallback; }
}
