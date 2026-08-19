import Link from "next/link";

import { ServiceState } from "@/components/service-state";
import { LogoutButton } from "@/features/auth/logout-button";

const navigation: ReadonlyArray<{ href: string; label: string; roles?: readonly string[] }> = [
  { href: "/", label: "总览", roles: ["admin", "operator"] },
  { href: "/products", label: "商品", roles: ["admin", "operator", "designer"] },
  { href: "/production/new", label: "套图生产", roles: ["admin", "operator"] },
  { href: "/bulk", label: "批量生产", roles: ["admin", "operator"] },
  { href: "/talent", label: "模特资产", roles: ["admin", "operator", "designer"] },
  { href: "/fashion/new", label: "服饰试穿", roles: ["admin", "operator"] },
  { href: "/editing", label: "单图微调", roles: ["admin", "operator", "designer"] },
  { href: "/templates", label: "模板中心", roles: ["admin", "designer"] },
  { href: "/analytics", label: "成本运营", roles: ["admin", "operator"] },
  { href: "/models", label: "模型", roles: ["admin"] },
  { href: "/batches", label: "批次", roles: ["admin", "operator", "reviewer"] },
  { href: "/review", label: "审核", roles: ["admin", "reviewer"] },
  { href: "/admin/users", label: "用户治理", roles: ["admin"] },
  { href: "/admin/audit", label: "审计记录", roles: ["admin"] },
];

function Navigation({ roles, mobile = false }: { roles: string[]; mobile?: boolean }) {
  const visible = navigation.filter((item) => item.roles?.some((role) => roles.includes(role)));
  return (
    <nav aria-label={mobile ? "移动端中台主导航" : "中台主导航"} className={mobile ? "mobile-nav-list" : "grid gap-1"}>
      {visible.map((item) => <Link key={item.href} href={item.href} className="nav-link">{item.label}</Link>)}
    </nav>
  );
}

export function AppShell({ children, email, roles }: { children: React.ReactNode; email: string; roles: string[] }) {
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
      <a className="skip-link" href="#main-content">跳到主要内容</a>
      <aside className="hidden border-r border-white/10 bg-[#0d101b] p-6 lg:block lg:min-h-screen">
        <Link href="/" className="mb-9 flex items-center gap-3"><span className="brand-mark">A</span><span className="font-semibold">AI 生图中台</span></Link>
        <Navigation roles={roles} />
        <div className="mt-9 border-t border-white/10 pt-5 text-xs text-slate-500">
          <p>当前账户</p>
          <p className="mt-1 truncate text-slate-300" title={email}>{email}</p>
          <LogoutButton />
        </div>
      </aside>
      <div className="min-w-0">
        <header className="border-b border-white/10 px-5 py-4 lg:px-10">
          <div className="flex items-center justify-between gap-4">
            <Link href="/" className="flex items-center gap-3 lg:hidden"><span className="brand-mark">A</span><span className="font-semibold">AI 生图中台</span></Link>
            <p className="hidden text-xs uppercase tracking-[0.18em] text-slate-500 lg:block">Production control room</p>
            <ServiceState />
          </div>
          <details className="mobile-nav mt-4 lg:hidden">
            <summary>打开功能导航</summary>
            <Navigation roles={roles} mobile />
            <div className="mobile-account"><span title={email}>{email}</span><LogoutButton /></div>
          </details>
        </header>
        <main id="main-content" className="p-5 sm:p-6 lg:p-10" tabIndex={-1}>{children}</main>
      </div>
    </div>
  );
}
