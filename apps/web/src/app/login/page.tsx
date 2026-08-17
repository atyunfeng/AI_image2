import { LoginForm } from "@/features/auth/login-form";

export default function LoginPage() {
  return <main className="grid min-h-screen place-items-center p-6"><section className="panel w-full max-w-md p-8"><div className="mb-10 flex items-center gap-3"><span className="brand-mark">A</span><div><p className="text-xs uppercase tracking-[0.3em] text-orange-300">AI Commerce Studio</p><h1 className="text-2xl font-semibold">生图中台</h1></div></div><p className="mb-6 text-sm text-slate-400">登录后管理商品真值、模型、生成批次与人工审核。</p><LoginForm /></section></main>;
}
