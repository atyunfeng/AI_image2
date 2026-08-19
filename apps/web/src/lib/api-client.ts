import "server-only";
import { cookies } from "next/headers";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(public readonly status: number, public readonly path: string) {
    super(`API ${status}: ${path}`);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = (await cookies()).get("aiimage_session")?.value;
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers, cache: "no-store" });
  if (!response.ok) throw new ApiError(response.status, path);
  return response.json() as Promise<T>;
}

export async function safeApiFetch<T>(path: string, fallback: T): Promise<T> {
  try {
    return await apiFetch<T>(path);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return fallback;
    throw error;
  }
}

export type Readiness = {
  status: "ready" | "degraded";
  checks: Record<string, boolean>;
};

export async function apiReadiness(): Promise<Readiness> {
  try {
    const response = await fetch(`${API_BASE_URL}/health/ready`, { cache: "no-store" });
    const payload = (await response.json()) as Readiness;
    return payload;
  } catch {
    return { status: "degraded", checks: {} };
  }
}
