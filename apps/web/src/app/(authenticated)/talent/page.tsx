import Link from "next/link";

import { ProfileList } from "@/features/talent/profile-list";
import { safeApiFetch } from "@/lib/api-client";
import { ModelProfile } from "@/lib/types";

export default async function TalentPage() {
  const profiles = await safeApiFetch<ModelProfile[]>("/model-profiles", []);
  return <div className="space-y-7"><div className="flex flex-wrap items-end justify-between gap-4"><div><p className="eyebrow">AUTHORIZED TALENT</p><h1 className="page-title">模特资产</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">集中管理系统虚拟模特和品牌授权真人模特。参考图作为不可变资产参与多角度生成与虚拟试穿。</p></div><Link className="primary-button min-h-11" href="/talent/new">新建模特</Link></div><ProfileList profiles={profiles} /></div>;
}
