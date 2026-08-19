import Link from "next/link";
import Image from "next/image";

import { BatchStatus } from "@/features/batches/batch-status";
import { QualityEvidence } from "@/features/templates/quality-evidence";
import { safeApiFetch } from "@/lib/api-client";
import { Batch, ProductionPlan, QualityRun } from "@/lib/types";

export default async function ProductionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [plan, allBatches] = await Promise.all([
    safeApiFetch<ProductionPlan | null>(`/production-plans/${id}`, null),
    safeApiFetch<Batch[]>("/batches", []),
  ]);
  if (!plan) return <p className="empty-copy">套图计划不存在或服务暂不可用。</p>;
  const batches = allBatches.filter((batch) => batch.production_plan_id === id);
  const qualityByBatch = new Map<string, QualityRun | null>(
    await Promise.all(batches.map(async (batch) => [batch.id, await safeApiFetch<QualityRun | null>(`/batches/${batch.id}/quality`, null)] as const)),
  );
  return (
    <div className="space-y-7">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">PRODUCTION {id.slice(0, 8)}</p>
          <h1 className="page-title">套图生成进度</h1>
          <p className="mt-2 font-mono text-xs text-slate-500">规则哈希 {plan.compiler_hash}</p>
        </div>
        <Link className="secondary-button" href="/production/new">新建套图</Link>
        {batches.length > 0 && batches.every((batch) => ["approved", "exported"].includes(batch.status)) && <a className="primary-button" href={`/api/backend/production-plans/${id}/export.zip`}>导出整套图片</a>}
      </div>
      <div className="grid gap-5 lg:grid-cols-3">
        {plan.items.map((item) => {
          const batch = batches.find((value) => value.production_plan_item_id === item.id);
          const quality = batch ? qualityByBatch.get(batch.id) ?? null : null;
          return (
            <article className="panel overflow-hidden p-5" key={item.id}>
              <div className="flex items-start justify-between gap-3">
                <div><h2 className="section-title">{item.label}</h2><p className="mt-1 text-xs text-slate-500">{item.width} × {item.height}</p></div>
                {batch ? <BatchStatus status={batch.status} /> : <span className="version-chip">待创建</span>}
              </div>
              <div className="relative mt-4 aspect-square overflow-hidden rounded-xl border border-white/10 bg-[#090b12]">
                {batch?.output_asset_id ? <Image unoptimized fill className="object-contain" sizes="(min-width: 1024px) 30vw, 100vw" src={`/api/backend/assets/${batch.output_asset_id}/content`} alt={`${item.label}生成结果`} /> : <div className="grid h-full place-items-center px-6 text-center text-xs text-slate-600">生成任务正在排队或执行</div>}
              </div>
              <QualityEvidence quality={quality} />
              {batch && <Link className="secondary-button mt-4 w-full" href={`/batches/${batch.id}`}>查看与审核</Link>}
            </article>
          );
        })}
      </div>
    </div>
  );
}
