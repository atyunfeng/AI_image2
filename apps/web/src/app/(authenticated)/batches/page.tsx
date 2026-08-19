import Link from "next/link";

import { BatchList } from "@/features/batches/batch-list";
import { safeApiFetch } from "@/lib/api-client";
import { Batch } from "@/lib/types";

const pageSize = 50;
const statuses = ["queued", "retry_queued", "running", "review_pending", "approved", "rejected", "failed", "exported"];

export default async function BatchesPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const incoming = await searchParams;
  const page = Math.max(1, Number(incoming.page) || 1);
  const status = typeof incoming.status === "string" && statuses.includes(incoming.status) ? incoming.status : "";
  const params = new URLSearchParams({ limit: String(pageSize), offset: String((page - 1) * pageSize) });
  if (status) params.set("status", status);
  const batches = await safeApiFetch<Batch[]>(`/batches?${params}`, []);
  const pageHref = (target: number) => `/batches?${new URLSearchParams({ ...(status ? { status } : {}), page: String(target) })}`;

  return <div className="space-y-7">
    <div className="flex flex-wrap items-end justify-between gap-4"><div><p className="eyebrow">GENERATION QUEUE</p><h1 className="page-title">生成批次</h1></div><Link href="/batches/new" className="primary-button">新建批次</Link></div>
    <form className="panel flex flex-col gap-3 p-4 sm:flex-row sm:items-end" method="get"><div className="min-w-0 flex-1"><label className="field-label mb-2" htmlFor="batch-status">按状态筛选</label><select className="field" id="batch-status" name="status" defaultValue={status}><option value="">全部状态</option>{statuses.map((value) => <option key={value} value={value}>{value}</option>)}</select></div><button className="secondary-button" type="submit">应用筛选</button></form>
    <section className="panel p-6"><BatchList batches={batches} /></section>
    <nav className="flex items-center justify-between" aria-label="批次分页"><span className="text-sm text-slate-500">第 {page} 页 · 每页最多 {pageSize} 条</span><div className="flex gap-2">{page > 1 ? <Link className="secondary-button" href={pageHref(page - 1)}>上一页</Link> : <span className="secondary-button opacity-40" aria-disabled="true">上一页</span>}{batches.length === pageSize ? <Link className="secondary-button" href={pageHref(page + 1)}>下一页</Link> : <span className="secondary-button opacity-40" aria-disabled="true">下一页</span>}</div></nav>
  </div>;
}
