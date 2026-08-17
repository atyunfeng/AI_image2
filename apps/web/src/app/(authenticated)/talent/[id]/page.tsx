/* eslint-disable @next/next/no-img-element */
import Link from "next/link";

import { ModelReferenceUpload } from "@/features/talent/model-reference-upload";
import { safeApiFetch } from "@/lib/api-client";
import { ModelProfile } from "@/lib/types";

const viewLabels = { front: "正面", side: "侧面", back: "背面", half_body: "半身", full_body: "全身" };

export default async function TalentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const profile = await safeApiFetch<ModelProfile | null>(`/model-profiles/${id}`, null);
  if (!profile) return <p className="empty-copy">模特档案不存在或服务暂不可用。</p>;
  return <div className="space-y-7"><div className="flex flex-wrap items-end justify-between gap-4"><div><p className="eyebrow">{profile.profile_type === "system_virtual" ? "SYSTEM VIRTUAL" : "BRAND AUTHORIZED"}</p><h1 className="page-title">{profile.name}</h1><div className="mt-3 flex flex-wrap gap-2"><span className={profile.is_selectable ? "status-pill" : "failure-pill"}>{profile.is_selectable ? "可用于生图" : "待上传参考图或授权无效"}</span>{profile.authorization_expires_on && <span className="version-chip">授权至 {profile.authorization_expires_on}</span>}</div></div><Link className="secondary-button" href="/fashion/new">创建服饰任务</Link></div><div className="grid gap-6 xl:grid-cols-[1fr_340px]"><section className="panel p-6"><h2 className="section-title mb-5">不可变模特参考图</h2>{profile.references.length ? <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{profile.references.map((reference) => <article className="overflow-hidden rounded-xl border border-white/10" key={reference.id}><img className="aspect-[3/4] w-full bg-white object-contain" src={`/api/backend/assets/${reference.asset_id}/content`} alt={`${viewLabels[reference.view]}模特参考图`} /><div className="p-3"><p className="text-sm text-slate-200">{viewLabels[reference.view]}</p><p className="mt-1 font-mono text-[11px] text-slate-500">{reference.sha256.slice(0, 12)}</p></div></article>)}</div> : <p className="empty-copy">至少上传一个参考视角后才可选择该模特；多角度一致性建议正面、侧面、背面齐全。</p>}</section><aside className="panel h-fit p-6"><h2 className="section-title mb-5">新增参考视角</h2><ModelReferenceUpload profileId={id} /></aside></div></div>;
}
