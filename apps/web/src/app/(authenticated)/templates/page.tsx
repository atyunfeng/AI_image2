import { TemplateManager } from "@/features/templates/template-manager";
import { safeApiFetch } from "@/lib/api-client";
import { ManagedTemplatePack } from "@/lib/types";

export default async function TemplatesPage() {
  const packs = await safeApiFetch<ManagedTemplatePack[]>("/template-packs/manage", []);
  return <div className="space-y-7"><div><p className="eyebrow">IMMUTABLE TEMPLATE CONTROL</p><h1 className="page-title">模板中心</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">平台、品类和品牌规则通过草稿版本演进；发布后不覆盖，只能复制为下一版。</p></div><TemplateManager initialPacks={packs} /></div>;
}
