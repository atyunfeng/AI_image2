"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { BulkJob, ModelConfiguration, TemplatePack } from "@/lib/types";

export function BulkProduction({ models, packs, initialJobs }: { models: ModelConfiguration[]; packs: TemplatePack[]; initialJobs: BulkJob[] }) {
  const eligibleModels = models.filter((model) => model.is_enabled && model.capabilities.includes("reference_to_image"));
  const categories = packs.filter((pack) => pack.kind === "category");
  const brands = packs.filter((pack) => pack.kind === "brand");
  const [jobs, setJobs] = useState(initialJobs);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const active = jobs.filter((job) => ["pending", "processing"].includes(job.status));
    if (!active.length) return;
    const timer = window.setInterval(async () => {
      const updates = await Promise.all(active.map(async (job) => {
        const response = await fetch(`/api/backend/bulk-jobs/${job.id}`, { cache: "no-store" });
        return response.ok ? await response.json() as BulkJob : job;
      }));
      const byId = new Map(updates.map((job) => [job.id, job]));
      setJobs((current) => current.map((job) => byId.get(job.id) ?? job));
    }, 2000);
    return () => window.clearInterval(timer);
  }, [jobs]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    const response = await fetch("/api/backend/bulk-jobs/import", { method: "POST", body: new FormData(event.currentTarget) });
    const body = await response.json().catch(() => ({ detail: "导入失败" }));
    if (response.ok) {
      setJobs((current) => [body, ...current]);
      setMessage(body.dry_run ? "预检已进入后台队列，完成后自动刷新结果。" : "批量任务已进入后台队列，失败行不会影响成功行。");
    } else setMessage(body.detail ?? "导入失败");
    setBusy(false);
  }

  return <div className="grid items-start gap-6 xl:grid-cols-[420px_1fr]">
    <section className="panel h-fit p-6"><div className="flex items-start justify-between gap-3"><div><p className="eyebrow">CSV / XLSX INTAKE</p><h2 className="section-title mt-2">批量生产入口</h2></div><a className="secondary-button text-xs" download="aiimage-bulk-template.csv" href={'data:text/csv;charset=utf-8,sku,name,brand,category,platform_slug,mode,reference_asset_id,reference_view%0AEXAMPLE-001,%E5%95%86%E5%93%81%E5%90%8D,,apparel,jd-cn,strict,,front'}>下载模板</a></div>
      <form className="form-grid mt-6" onSubmit={submit} aria-busy={busy}>
        <div><label className="field-label mb-2" htmlFor="bulk-file">CSV 或 XLSX 文件</label><input className="field file:mr-3 file:rounded-lg file:border-0 file:bg-orange-400 file:px-3 file:py-1 file:text-[#19131a]" id="bulk-file" name="file" type="file" accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" required /></div>
        <div><label className="field-label mb-2" htmlFor="bulk-model">生图模型</label><select className="field" id="bulk-model" name="model_configuration_id" required>{eligibleModels.map((model) => <option key={model.id} value={model.id}>{model.name} · {model.model_id}</option>)}</select></div>
        <div className="grid gap-3 sm:grid-cols-2"><div><label className="field-label mb-2" htmlFor="bulk-category">品类包</label><select className="field" id="bulk-category" name="category_pack_version_id" required>{categories.map((pack) => <option key={pack.version_id} value={pack.version_id}>{pack.name}</option>)}</select></div><div><label className="field-label mb-2" htmlFor="bulk-brand">品牌包</label><select className="field" id="bulk-brand" name="brand_pack_version_id" required>{brands.map((pack) => <option key={pack.version_id} value={pack.version_id}>{pack.name}</option>)}</select></div></div>
        <label className="flex items-start gap-3 rounded-xl border border-white/10 p-3 text-sm text-slate-300"><input className="mt-1" type="checkbox" name="dry_run" value="true" /><span>仅预检文件<small className="mt-1 block text-slate-500">保存逐行校验结果，但不创建商品、套图和生图任务。</small></span></label>
        <button className="primary-button" disabled={busy || !eligibleModels.length}>{busy ? "处理中…" : "上传并创建任务"}</button>
        <p className="text-xs leading-5 text-slate-500">已有 SKU 可复用原参考图；新 SKU 必须填写已上传的 reference_asset_id。单次最多 500 行、2 MiB。</p>
        <p role="status" aria-live="polite" className="min-h-5 text-sm text-orange-200">{message}</p>
      </form>
    </section>
    <section className="panel min-w-0 overflow-hidden p-6"><div className="mb-5 flex items-end justify-between"><div><p className="eyebrow">JOB LEDGER</p><h2 className="section-title mt-2">批量作业记录</h2></div><span className="version-chip">{jobs.length} 个作业</span></div>
      {!jobs.length ? <p className="empty-copy">还没有批量作业。</p> : <div className="space-y-5">{jobs.map((job) => <article key={job.id} className="rounded-2xl border border-white/8 bg-black/10 p-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-semibold">{job.filename}</p><p className="mt-1 font-mono text-xs text-slate-500">{job.id.slice(0, 8)} · {job.dry_run ? "预检" : "执行"}</p></div><div className="flex gap-2"><span className="status-pill">{job.status}</span>{job.failed_rows > 0 && <a className="failure-pill" href={`/api/backend/bulk-jobs/${job.id}/errors.csv`}>下载 {job.failed_rows} 条错误</a>}</div></div><div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs"><div className="plan-slot min-h-0"><strong className="block text-lg text-white">{job.total_rows}</strong><span className="text-slate-500">总行数</span></div><div className="plan-slot min-h-0"><strong className="block text-lg text-emerald-300">{job.succeeded_rows}</strong><span className="text-slate-500">成功</span></div><div className="plan-slot min-h-0"><strong className="block text-lg text-red-300">{job.failed_rows}</strong><span className="text-slate-500">失败</span></div></div><div className="mt-3 overflow-x-auto"><table className="data-table min-w-[640px]"><thead><tr><th>行</th><th>SKU</th><th>平台</th><th>状态</th><th>结果</th></tr></thead><tbody>{job.rows.map((row) => <tr key={row.id}><td>{row.row_number}</td><td>{row.sku}</td><td>{row.input_data.platform_slug}</td><td>{row.status}</td><td>{row.production_plan_id ? <Link className="text-orange-300" href={`/production/${row.production_plan_id}`}>查看套图</Link> : <span className="text-red-300">{row.error ?? "—"}</span>}</td></tr>)}</tbody></table></div></article>)}</div>}
    </section>
  </div>;
}
