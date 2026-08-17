"use client";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { LoginInput, LoginResult, loginAction } from "@/lib/session";

export function LoginForm({ login = loginAction }: { login?: (input: LoginInput) => Promise<LoginResult> }) {
  const router = useRouter();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget); setPending(true);
    const result = await login({ email: String(form.get("email")), password: String(form.get("password")) }); setPending(false);
    if (!result.ok) return setError(result.message ?? "登录失败");
    router.push("/"); router.refresh();
  }
  return <form onSubmit={submit} className="space-y-5"><label className="field-label" htmlFor="email">邮箱</label><input className="field" id="email" name="email" type="email" required /><label className="field-label" htmlFor="password">密码</label><input className="field" id="password" name="password" type="password" required />{error && <p role="alert" className="text-sm text-red-400">{error}</p>}<button className="primary-button w-full" disabled={pending} type="submit">{pending ? "正在登录…" : "登录"}</button></form>;
}
