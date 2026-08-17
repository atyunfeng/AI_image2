import Link from "next/link";

import { ModelProfile } from "@/lib/types";

const typeLabels = { system_virtual: "系统虚拟", brand_authorized: "品牌授权" };

export function ProfileList({ profiles }: { profiles: ModelProfile[] }) {
  if (!profiles.length) return <p className="empty-copy">还没有模特资产。创建后上传正面、侧面和背面参考图。</p>;
  return <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{profiles.map((profile) => <Link className="panel block p-5 hover:border-orange-300/30" href={`/talent/${profile.id}`} key={profile.id}><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold">{profile.name}</p><p className="mt-1 text-xs text-slate-500">{typeLabels[profile.profile_type]}</p></div><span className={profile.is_selectable ? "status-pill" : "failure-pill"}>{profile.is_selectable ? "可用于生图" : "待完善"}</span></div><div className="mt-5 flex items-center justify-between text-xs text-slate-500"><span>{profile.references.length} 个参考视角</span><span>{profile.authorization_expires_on ? `有效至 ${profile.authorization_expires_on}` : "无需授权到期日"}</span></div></Link>)}</div>;
}
