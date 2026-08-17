/* eslint-disable @next/next/no-img-element */
import { BatchActions } from "@/features/batches/batch-actions";
import { BatchStatus } from "@/features/batches/batch-status";
import { StartEditButton } from "@/features/editing/start-edit-button";
import { ReviewPanel } from "@/features/review/review-panel";
import { safeApiFetch } from "@/lib/api-client";
import { Batch, ExportRecord } from "@/lib/types";

export default async function BatchDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [batch, exports] = await Promise.all([
    safeApiFetch<Batch | null>(`/batches/${id}`, null),
    safeApiFetch<ExportRecord[]>(`/batches/${id}/exports`, []),
  ]);
  if (!batch) return <p className="empty-copy">批次不存在或服务暂不可用。</p>;
  return <div className="space-y-7"><div className="flex items-end justify-between"><div><p className="eyebrow">BATCH {id.slice(0, 8)}</p><h1 className="page-title">生成与审核</h1></div><BatchStatus status={batch.status} /></div><div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]"><div className="space-y-6"><section className="panel p-6"><div className="aspect-square overflow-hidden rounded-2xl border border-white/10 bg-[#090b12]">{batch.output_asset_id ? <img src={`/api/backend/assets/${batch.output_asset_id}/content`} alt="生成结果" className="h-full w-full object-contain" /> : <div className="grid h-full place-items-center text-slate-600">模型正在处理 · 页面自动刷新</div>}</div><dl className="mt-5 grid gap-3 text-sm sm:grid-cols-2"><div><dt className="text-slate-500">视角 / 模式</dt><dd>{batch.requested_view} / {batch.mode}</dd></div><div><dt className="text-slate-500">尺寸</dt><dd>{batch.width} × {batch.height}</dd></div><div><dt className="text-slate-500">请求 ID</dt><dd className="break-all font-mono text-xs">{batch.provider_request_id ?? "—"}</dd></div><div><dt className="text-slate-500">成本</dt><dd>{batch.estimated_cost_minor ?? 0} minor</dd></div></dl><StartEditButton batchId={id} disabled={!batch.output_asset_id} /></section>{exports.length > 0 && <section className="panel p-6"><h2 className="section-title">导出历史</h2><div className="mt-4 space-y-3">{exports.map((record) => <a className="row-card" href={`/api/backend/assets/${record.archive_asset_id}/content`} key={record.id}><span>{new Date(record.created_at).toLocaleString("zh-CN")}</span><span className="row-card-main font-mono text-xs">{record.manifest_sha256.slice(0, 16)}</span><span className="status-pill">ZIP</span></a>)}</div></section>}</div><div className="space-y-6"><ReviewPanel batch={batch} /><BatchActions batch={batch} /></div></div></div>;
}
