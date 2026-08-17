"use server";
import { cookies } from "next/headers";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000/api/v1";
export type LoginInput = { email: string; password: string };
export type LoginResult = { ok: boolean; message?: string };

export async function loginAction(input: LoginInput): Promise<LoginResult> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input), cache: "no-store" });
  if (!response.ok) return { ok: false, message: "邮箱或密码不正确" };
  const payload = (await response.json()) as { access_token: string };
  (await cookies()).set("aiimage_session", payload.access_token, { httpOnly: true, sameSite: "strict", secure: process.env.NODE_ENV === "production", path: "/", maxAge: 60 * 60 * 8 });
  return { ok: true };
}

export async function logoutAction(): Promise<void> { (await cookies()).delete("aiimage_session"); }
