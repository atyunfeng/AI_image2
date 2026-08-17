import { BulkProduction } from "@/features/bulk/bulk-production";
import { safeApiFetch } from "@/lib/api-client";
import { BulkJob, ModelConfiguration, TemplatePack } from "@/lib/types";

export default async function BulkPage() {
  const [models, packs, jobs] = await Promise.all([
    safeApiFetch<ModelConfiguration[]>("/models", []),
    safeApiFetch<TemplatePack[]>("/template-packs", []),
    safeApiFetch<BulkJob[]>("/bulk-jobs", []),
  ]);
  return <div className="space-y-7"><div><p className="eyebrow">PRODUCTION SCALE</p><h1 className="page-title">批量生产</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">用一份 CSV 批量编译多 SKU、多平台图片计划。逐行隔离失败，成功任务继续进入现有质检、审核与导出闭环。</p></div><BulkProduction models={models} packs={packs} initialJobs={jobs} /></div>;
}
