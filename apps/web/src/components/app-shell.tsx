import Link from "next/link";

const navigation: ReadonlyArray<{ href: string; label: string; roles?: readonly string[] }> = [
  { href: "/", label: "总览" },
  { href: "/products", label: "商品" },
  { href: "/production/new", label: "套图生产" },
  { href: "/bulk", label: "批量生产" },
  { href: "/talent", label: "模特资产" },
  { href: "/fashion/new", label: "服饰试穿" },
  { href: "/editing", label: "单图微调" },
  { href: "/templates", label: "模板中心", roles: ["admin", "designer"] },
  { href: "/analytics", label: "成本运营" },
  { href: "/models", label: "模型" },
  { href: "/batches", label: "批次" },
  { href: "/review", label: "审核" },
  { href: "/admin/users", label: "用户治理", roles: ["admin"] },
  { href: "/admin/audit", label: "审计记录", roles: ["admin"] },
];

export function AppShell({ children, email, roles }: { children: React.ReactNode; email: string; roles: string[] }) {
  const visibleNavigation = navigation.filter((item) => !item.roles || item.roles.some((role) => roles.includes(role)));
  return <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]"><aside className="border-b border-white/10 bg-[#0d101b] p-6 lg:min-h-screen lg:border-b-0 lg:border-r"><Link href="/" className="mb-10 flex items-center gap-3"><span className="brand-mark">A</span><span className="font-semibold">AI 生图中台</span></Link><nav aria-label="中台主导航" className="flex gap-2 overflow-auto lg:flex-col">{visibleNavigation.map((item, index) => <Link key={item.href} href={item.href} className="nav-link"><span className="text-xs text-orange-300">{String(index + 1).padStart(2, "0")}</span>{item.label}</Link>)}</nav><div className="mt-10 hidden border-t border-white/10 pt-5 text-xs text-slate-500 lg:block"><p>当前账户</p><p className="mt-1 truncate text-slate-300">{email}</p></div></aside><div className="min-w-0"><header className="flex min-h-16 items-center justify-between gap-4 border-b border-white/10 px-6 py-3 lg:px-10"><p className="text-xs uppercase tracking-[0.24em] text-slate-500">M6 · Full product operations</p><span className="status-pill">系统在线</span></header><main className="p-6 lg:p-10">{children}</main></div></div>;
}
