import Link from "next/link";
import { redirect } from "next/navigation";

import { apiFetch, safeApiFetch } from "@/lib/api-client";
import { Batch, ModelConfiguration, OperationsReport, Product } from "@/lib/types";

const emptyOperations: OperationsReport = { generated_at: "", queued_count: 0, running_count: 0, review_pending_count: 0, failed_count: 0, total_calls: 0, succeeded_calls: 0, retry_calls: 0, success_rate: 0, retry_rate: 0, latency_p50_ms: 0, latency_p95_ms: 0, failure_classes: [], cost_groups: [], alerts: [] };

export default async function DashboardPage() {
  const user = await apiFetch<{ roles: string[] }>("/auth/me");
  if (!user.roles.some((role) => ["admin", "operator"].includes(role))) {
    redirect(user.roles.includes("reviewer") ? "/review" : "/editing");
  }
  const [products, models, batches, operations] = await Promise.all([safeApiFetch<Product[]>("/products", []), safeApiFetch<ModelConfiguration[]>("/models", []), safeApiFetch<Batch[]>("/batches", []), safeApiFetch<OperationsReport>("/analytics/operations", emptyOperations)]);
  return <div className="space-y-8"><section className="flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><p className="eyebrow">CONTROL ROOM</p><h1 className="page-title">电商视觉生产线</h1><p className="mt-3 max-w-2xl text-slate-400">从商品真值与参考图出发，统一编排生图模型、人工审核和可追溯导出。</p></div><Link href="/batches/new" className="primary-button">新建生成批次</Link></section>
    {operations.alerts.length > 0 && <section className="space-y-3" aria-label="需要处理的运营告警">{operations.alerts.map((alert) => <Link className="failure-note block" href={alert.action_url} key={alert.code}><strong>{alert.title}</strong><span className="ml-2">{alert.detail}</span></Link>)}</section>}
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[["商品档案", products.length], ["可用模型", models.filter((model) => model.is_enabled).length], ["排队 / 执行", `${operations.queued_count} / ${operations.running_count}`], ["待审核 / 失败", `${operations.review_pending_count} / ${operations.failed_count}`]].map(([label, value]) => <div className="metric-card" key={label}><p>{label}</p><strong>{value}</strong></div>)}</section>
    <section className="panel p-6"><div className="mb-5 flex items-center justify-between"><h2 className="section-title">最近批次</h2><Link className="text-sm text-orange-300" href="/batches">查看全部 →</Link></div>{batches.length ? <div className="space-y-3">{batches.slice(0, 5).map((batch) => <Link href={`/batches/${batch.id}`} key={batch.id} className="row-card"><span className="font-mono text-xs text-slate-500">{batch.id.slice(0, 8)}</span><span>{batch.requested_view}</span><span className="status-pill">{batch.status}</span></Link>)}</div> : <p className="empty-copy">还没有生成批次。先录入商品和模型，再启动第一张商品图。</p>}</section>
  </div>;
}
