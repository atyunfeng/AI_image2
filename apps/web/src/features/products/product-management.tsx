"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Product, TruthAnchor } from "@/lib/types";

export function ProductManagement({ product }: { product: Product }) {
  const router = useRouter();
  const [anchors, setAnchors] = useState<TruthAnchor[]>(product.truth_anchors ?? []);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function update(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const form = new FormData(event.currentTarget);
    const response = await fetch(`/api/backend/products/${product.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: form.get("name"), category: form.get("category"), brand: form.get("brand") || null }),
    });
    setMessage(response.ok ? "商品资料已更新。" : "更新失败，请检查输入。 ");
    setBusy(false);
    if (response.ok) router.refresh();
  }

  async function saveAnchor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    try {
      const raw = String(new FormData(event.currentTarget).get("document") ?? "{}");
      const response = await fetch(`/api/backend/products/${product.id}/truth-anchors`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document: JSON.parse(raw) }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "保存失败");
      setAnchors((current) => [body, ...current]);
      setMessage(`真值锚点 v${body.version} 已保存，历史版本未被覆盖。`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "JSON 格式无效");
    } finally {
      setBusy(false);
    }
  }

  async function analyze() {
    setBusy(true);
    const response = await fetch(`/api/backend/products/${product.id}/truth-anchors/analyze`, { method: "POST" });
    const body = await response.json().catch(() => ({ detail: "分析失败" }));
    if (response.ok) {
      setAnchors((current) => [body, ...current]);
      setMessage(`已从参考图生成确定性真值锚点 v${body.version}。`);
    } else setMessage(body.detail ?? "分析失败");
    setBusy(false);
  }

  async function archive() {
    if (!window.confirm(`归档 ${product.sku}？素材和历史记录会保留。`)) return;
    setBusy(true);
    const response = await fetch(`/api/backend/products/${product.id}`, { method: "DELETE" });
    if (response.ok) router.push("/products");
    else setMessage("归档失败。");
    setBusy(false);
  }

  return <div className="space-y-6">
    <section className="panel p-6"><div className="mb-5 flex items-center justify-between gap-3"><h2 className="section-title">商品资料</h2><button className="failure-pill" type="button" onClick={archive} disabled={busy}>归档商品</button></div>
      <form className="form-grid" onSubmit={update} aria-busy={busy}><div><label className="field-label mb-2" htmlFor="product-name">商品名称</label><input className="field" id="product-name" name="name" defaultValue={product.name} required /></div><div><label className="field-label mb-2" htmlFor="product-brand">品牌</label><input className="field" id="product-brand" name="brand" defaultValue={product.brand ?? ""} autoComplete="organization" /></div><div><label className="field-label mb-2" htmlFor="product-category">品类</label><select className="field" id="product-category" name="category" defaultValue={product.category}><option value="apparel">服装</option><option value="shoes">鞋靴</option><option value="hats">帽饰</option><option value="other">其他</option></select></div><button className="secondary-button" disabled={busy}>保存资料</button></form>
    </section>
    <section className="panel p-6"><div className="mb-5 flex flex-wrap items-center justify-between gap-3"><div><p className="eyebrow">TRUTH LEDGER</p><h2 className="section-title mt-2">商品真值锚点</h2></div><button className="secondary-button" type="button" onClick={analyze} disabled={busy || !product.references?.length}>分析参考图</button></div>
      <form className="form-grid" onSubmit={saveAnchor}><div><label className="field-label mb-2" htmlFor="truth-document">人工确认 JSON</label><textarea className="field min-h-32 font-mono text-xs" id="truth-document" name="document" defaultValue={JSON.stringify(anchors[0]?.document ?? {}, null, 2)} spellCheck={false} /></div><button className="secondary-button" disabled={busy}>保存新版本</button></form>
      <div className="mt-5 space-y-3">{anchors.map((anchor) => <details key={anchor.id} className="plan-slot min-h-0"><summary className="cursor-pointer text-sm font-semibold">v{anchor.version} · {new Date(anchor.created_at).toLocaleString("zh-CN")}</summary><pre className="mt-3 overflow-x-auto text-xs leading-5 text-slate-400">{JSON.stringify(anchor.document, null, 2)}</pre></details>)}</div>
    </section>
    <p role="status" aria-live="polite" className="min-h-5 text-sm text-orange-200">{message}</p>
  </div>;
}
