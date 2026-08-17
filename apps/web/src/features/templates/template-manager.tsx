"use client";

import { FormEvent, useState } from "react";

import { ManagedTemplatePack } from "@/lib/types";

export function TemplateManager({ initialPacks }: { initialPacks: ManagedTemplatePack[] }) {
  const [packs, setPacks] = useState(initialPacks);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function createPack(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    try {
      const form = new FormData(event.currentTarget);
      const response = await fetch("/api/backend/template-packs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slug: form.get("slug"), name: form.get("name"), kind: form.get("kind"), rules: JSON.parse(String(form.get("rules"))) }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "创建失败");
      setPacks((current) => [...current, body]);
      setMessage("模板包草稿 v1 已创建。 ");
      event.currentTarget.reset();
    } catch (error) { setMessage(error instanceof Error ? error.message : "JSON 格式无效"); }
    finally { setBusy(false); }
  }

  async function newVersion(pack: ManagedTemplatePack, event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    try {
      const rules = JSON.parse(String(new FormData(event.currentTarget).get("rules")));
      const response = await fetch(`/api/backend/template-packs/${pack.id}/versions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ source_version_id: pack.versions[0]?.id, rules }) });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "创建版本失败");
      setPacks((current) => current.map((item) => item.id === pack.id ? { ...item, versions: [body, ...item.versions] } : item));
      setMessage(`${pack.name} v${body.version} 草稿已创建。`);
    } catch (error) { setMessage(error instanceof Error ? error.message : "JSON 格式无效"); }
    finally { setBusy(false); }
  }

  async function publish(packId: string, versionId: string) {
    setBusy(true);
    const response = await fetch(`/api/backend/template-pack-versions/${versionId}/publish`, { method: "POST" });
    const body = await response.json().catch(() => ({ detail: "发布失败" }));
    if (response.ok) {
      setPacks((current) => current.map((pack) => pack.id === packId ? { ...pack, versions: pack.versions.map((version) => version.id === versionId ? body : version) } : pack));
      setMessage(`v${body.version} 已发布，历史版本保持不可变。`);
    } else setMessage(body.detail ?? "发布失败");
    setBusy(false);
  }

  return <div className="grid items-start gap-6 xl:grid-cols-[360px_minmax(0,1fr)]"><section className="panel p-6"><p className="eyebrow">AUTHOR</p><h2 className="section-title mt-2">新建模板包</h2><form className="form-grid mt-6" onSubmit={createPack}><div><label className="field-label mb-2" htmlFor="pack-slug">唯一标识</label><input className="field" id="pack-slug" name="slug" pattern="[a-z0-9]+(?:-[a-z0-9]+)*" placeholder="brand-editorial" required /></div><div><label className="field-label mb-2" htmlFor="pack-name">名称</label><input className="field" id="pack-name" name="name" required /></div><div><label className="field-label mb-2" htmlFor="pack-kind">类型</label><select className="field" id="pack-kind" name="kind"><option value="platform">平台</option><option value="category">品类</option><option value="brand">品牌</option></select></div><div><label className="field-label mb-2" htmlFor="pack-rules">规则 JSON</label><textarea className="field min-h-40 font-mono text-xs" id="pack-rules" name="rules" defaultValue={'{\n  "prompt_suffix": ""\n}'} spellCheck={false} required /></div><button className="primary-button" disabled={busy}>创建草稿</button></form></section>
    <section className="min-w-0 space-y-5">{packs.map((pack) => <article className="panel p-6" key={pack.id}><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="eyebrow">{pack.kind}</p><h2 className="section-title mt-2">{pack.name}</h2><p className="mt-1 font-mono text-xs text-slate-500">{pack.slug}</p></div><span className="version-chip">{pack.versions.length} 个版本</span></div><div className="mt-5 overflow-x-auto"><table className="data-table min-w-[620px]"><thead><tr><th>版本</th><th>状态</th><th>来源</th><th>发布时间</th><th>操作</th></tr></thead><tbody>{pack.versions.map((version) => <tr key={version.id}><td>v{version.version}</td><td><span className={version.status === "draft" ? "failure-pill" : "status-pill"}>{version.status}</span></td><td>{version.source}</td><td>{version.published_at ? new Date(version.published_at).toLocaleString("zh-CN") : "—"}</td><td>{version.status === "draft" ? <button className="secondary-button py-2 text-xs" type="button" disabled={busy} onClick={() => publish(pack.id, version.id)}>发布</button> : "不可变"}</td></tr>)}</tbody></table></div><details className="mt-5"><summary className="cursor-pointer text-sm text-orange-200">基于最新版本创建草稿</summary><form className="form-grid mt-4" onSubmit={(event) => newVersion(pack, event)}><textarea className="field min-h-40 font-mono text-xs" name="rules" defaultValue={JSON.stringify(pack.versions[0]?.rules ?? {}, null, 2)} spellCheck={false} /><button className="secondary-button" disabled={busy}>保存为新版本</button></form></details></article>)}{!packs.length && <p className="empty-copy">暂无模板包。</p>}<p role="status" aria-live="polite" className="min-h-5 text-sm text-orange-200">{message}</p></section></div>;
}
