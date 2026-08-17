import Image from "next/image";
import Link from "next/link";

import { BatchStatus } from "@/features/batches/batch-status";
import { FashionEvidenceCard } from "@/features/fashion/fashion-evidence";
import { safeApiFetch } from "@/lib/api-client";
import { FashionEvidence, FashionPlan } from "@/lib/types";

const outputLabels: Record<string, string> = { product_front: "商品正面图", model_front: "模特正面图", model_side: "模特侧面图", model_back: "模特背面图", detail: "商品细节图", virtual_try_on: "虚拟试穿图" };

export default async function FashionPlanPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const plan = await safeApiFetch<FashionPlan | null>(`/fashion-plans/${id}`, null);
  if (!plan) return <p className="empty-copy">服饰任务不存在或服务暂不可用。</p>;
  const evidenceByBatch = new Map<string, FashionEvidence | null>(await Promise.all(plan.batches.map(async (batch) => [batch.id, await safeApiFetch<FashionEvidence | null>(`/fashion-plans/batches/${batch.id}/evidence`, null)] as const)));
  return <div className="space-y-7"><div className="flex flex-wrap items-end justify-between gap-4"><div><p className="eyebrow">FASHION {id.slice(0, 8)}</p><h1 className="page-title">服饰生成进度</h1><p className="mt-3 text-sm text-slate-400">{plan.category} · {plan.mode === "strict" ? "严格商品模式" : "创意补全模式"} · {plan.batches.length} 张</p></div><Link className="secondary-button" href="/fashion/new">新建服饰任务</Link></div><div className="grid gap-5 lg:grid-cols-2 2xl:grid-cols-3">{plan.batches.map((batch, index) => { const output = plan.requested_outputs[index] ?? batch.requested_view; const evidence = evidenceByBatch.get(batch.id) ?? null; return <article className="panel overflow-hidden p-5" key={batch.id}><div className="flex items-start justify-between gap-3"><div><h2 className="section-title">{outputLabels[output] ?? output}</h2><p className="mt-1 text-xs text-slate-500">{batch.capability} · {batch.width} × {batch.height}</p></div><BatchStatus status={batch.status} /></div><div className="relative mt-4 aspect-square overflow-hidden rounded-xl border border-white/10 bg-[#090b12]">{batch.output_asset_id ? <Image unoptimized fill className="object-contain" sizes="(min-width: 1536px) 30vw, (min-width: 1024px) 45vw, 100vw" src={`/api/backend/assets/${batch.output_asset_id}/content`} alt={`${outputLabels[output] ?? output}生成结果`} /> : <div className="grid h-full place-items-center px-6 text-center text-xs text-slate-600">生成任务正在排队或执行</div>}</div><FashionEvidenceCard evidence={evidence} />{batch.status === "failed" && batch.error_classification && <p className="failure-note mt-4">{batch.error_classification}</p>}<Link className="secondary-button mt-4 min-h-11 w-full" href={`/batches/${batch.id}`}>查看与人工审核</Link></article>; })}</div></div>;
}
