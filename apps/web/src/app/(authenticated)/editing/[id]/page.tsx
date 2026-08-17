import { EditWorkspace } from "@/features/editing/edit-workspace";
import { safeApiFetch } from "@/lib/api-client";
import { EditEvidence, EditProject, ModelConfiguration } from "@/lib/types";

export default async function EditProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [project, models] = await Promise.all([safeApiFetch<EditProject | null>(`/edit-projects/${id}`, null), safeApiFetch<ModelConfiguration[]>("/models", [])]);
  if (!project) return <p className="empty-copy">编辑项目不存在或服务暂不可用。</p>;
  const pairs = await Promise.all(project.revisions.map(async (revision) => [revision.id, await safeApiFetch<EditEvidence | null>(`/edit-projects/revisions/${revision.id}/evidence`, null)] as const));
  return <div className="space-y-7"><div><p className="eyebrow">EDIT PROJECT {id.slice(0, 8)}</p><h1 className="page-title">{project.name}</h1><p className="mt-3 text-sm text-slate-400">选择历史版本作为父节点，可创建并行编辑分支；撤销和重做只切换视图，不删除任何资产。</p></div><EditWorkspace project={project} models={models} evidence={Object.fromEntries(pairs)} /></div>;
}
