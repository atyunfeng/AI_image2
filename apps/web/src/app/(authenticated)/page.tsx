import Link from "next/link";
import { safeApiFetch } from "@/lib/api-client";
import { Batch, ModelConfiguration, Product } from "@/lib/types";

export default async function DashboardPage() {
  const [products, models, batches] = await Promise.all([safeApiFetch<Product[]>("/products", []), safeApiFetch<ModelConfiguration[]>("/models", []), safeApiFetch<Batch[]>("/batches", [])]);
  const reviewCount = batches.filter((batch) => batch.status === "review_pending").length;
  return <div className="space-y-8"><section className="flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><p className="eyebrow">CONTROL ROOM</p><h1 className="page-title">电商视觉生产线</h1><p className="mt-3 max-w-2xl text-slate-400">从商品真值与参考图出发，统一编排生图模型、人工审核和可追溯导出。</p></div><Link href="/batches/new" className="primary-button">新建生成批次</Link></section><section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[["商品档案",products.length],["可用模型",models.length],["生成批次",batches.length],["待人工审核",reviewCount]].map(([label,value])=><div className="metric-card" key={label}><p>{label}</p><strong>{value}</strong></div>)}</section><section className="panel p-6"><div className="mb-5 flex items-center justify-between"><h2 className="section-title">最近批次</h2><Link className="text-sm text-orange-300" href="/batches">查看全部 →</Link></div>{batches.length ? <div className="space-y-3">{batches.slice(0,5).map(batch=><Link href={`/batches/${batch.id}`} key={batch.id} className="row-card"><span className="font-mono text-xs text-slate-500">{batch.id.slice(0,8)}</span><span>{batch.requested_view}</span><span className="status-pill">{batch.status}</span></Link>)}</div>:<p className="empty-copy">还没有生成批次。先录入商品和模型，再启动第一张商品图。</p>}</section></div>;
}
