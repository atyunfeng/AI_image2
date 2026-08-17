import Link from "next/link";

import { safeApiFetch } from "@/lib/api-client";
import { EditProject } from "@/lib/types";

export default async function EditingPage() {
  const projects = await safeApiFetch<EditProject[]>("/edit-projects", []);
  return <div className="space-y-7"><div><p className="eyebrow">IMMUTABLE EDITS</p><h1 className="page-title">单图微调项目</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">从任意生成批次进入微调。每次蒙版、模型、参数和图层变更都会产生独立版本，不覆盖已审核图片。</p></div>{projects.length ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{projects.map((project) => <Link className="panel block p-5 hover:border-orange-300/30" href={`/editing/${project.id}`} key={project.id}><div className="flex items-start justify-between gap-3"><div><p className="font-semibold">{project.name}</p><p className="mt-1 text-xs text-slate-500">源批次 {project.source_batch_id.slice(0, 8)}</p></div><span className="version-chip">{project.revisions.length} 版</span></div><p className="mt-5 text-xs text-slate-400">最新：{project.revisions.at(-1)?.snapshot_label ?? "原始图"}</p></Link>)}</div> : <p className="empty-copy">还没有编辑项目。请先打开一张已生成图片，在审核页面选择“微调此图”。</p>}</div>;
}
