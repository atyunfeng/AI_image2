import { BatchList } from "@/features/batches/batch-list";
import { safeApiFetch } from "@/lib/api-client";
import { Batch } from "@/lib/types";

export default async function ReviewQueue() {
  const groups = await Promise.all(
    ["review_pending", "approved", "rejected"].map((status) =>
      safeApiFetch<Batch[]>(`/batches?status=${status}&limit=200`, []),
    ),
  );
  const batches = groups.flat();
  return <div className="space-y-7"><div><p className="eyebrow">HUMAN GATE</p><h1 className="page-title">人工审核队列</h1><p className="mt-3 text-slate-400">任何输出都不会绕过人工确认直接导出；每种状态展示最新 200 条。</p></div><section className="panel p-6"><BatchList batches={batches} /></section></div>;
}
