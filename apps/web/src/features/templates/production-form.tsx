"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { ModelConfiguration, Product, ProductionPlan, TemplatePack } from "@/lib/types";
import { PlanPreview } from "./plan-preview";

type Props = { products: Product[]; models: ModelConfiguration[]; packs: TemplatePack[] };

export function ProductionForm({ products, models, packs }: Props) {
  const router = useRouter();
  const platformPacks = useMemo(() => packs.filter((pack) => pack.kind === "platform"), [packs]);
  const categoryPacks = useMemo(() => packs.filter((pack) => pack.kind === "category"), [packs]);
  const brandPacks = useMemo(() => packs.filter((pack) => pack.kind === "brand"), [packs]);
  const eligibleModels = models.filter((model) => model.is_enabled && model.capabilities.includes("reference_to_image"));
  const [plan, setPlan] = useState<ProductionPlan | null>(null);
  const [modelId, setModelId] = useState(eligibleModels[0]?.id ?? "");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState<"compile" | "execute" | null>(null);

  async function compile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy("compile");
    setMessage("");
    setPlan(null);
    const data = new FormData(event.currentTarget);
    const response = await fetch("/api/backend/production-plans/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_id: data.get("product_id"),
        platform_pack_version_id: data.get("platform_pack_version_id"),
        category_pack_version_id: data.get("category_pack_version_id"),
        brand_pack_version_id: data.get("brand_pack_version_id"),
        mode: data.get("mode"),
      }),
    });
    if (response.ok) {
      setPlan(await response.json());
      setMessage("套图规则编译完成，请核对图片槽位和版本后执行。");
    } else {
      const body = await response.json().catch(() => ({ detail: "编译失败" }));
      setMessage(body.detail ?? "编译失败，请检查商品参考图和规则包。");
    }
    setBusy(null);
  }

  async function execute() {
    if (!plan || !modelId) return;
    setBusy("execute");
    setMessage("");
    const response = await fetch(`/api/backend/production-plans/${plan.id}/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model_configuration_id: modelId }),
    });
    if (response.ok) {
      router.push(`/production/${plan.id}`);
      router.refresh();
      return;
    }
    const body = await response.json().catch(() => ({ detail: "执行失败" }));
    setMessage(body.detail ?? "套图任务启动失败。");
    setBusy(null);
  }

  return (
    <div>
      <form className="form-grid" onSubmit={compile} aria-busy={busy === "compile"}>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="field-label mb-2" htmlFor="product_id">商品 SKU</label>
            <select className="field" id="product_id" name="product_id" required>
              {products.map((product) => <option key={product.id} value={product.id}>{product.sku} · {product.name}</option>)}
            </select>
          </div>
          <div>
            <label className="field-label mb-2" htmlFor="platform_pack_version_id">目标平台</label>
            <select className="field" id="platform_pack_version_id" name="platform_pack_version_id" required>
              {platformPacks.map((pack) => <option key={pack.version_id} value={pack.version_id}>{pack.name} · v{pack.version}</option>)}
            </select>
          </div>
          <div>
            <label className="field-label mb-2" htmlFor="category_pack_version_id">品类套图</label>
            <select className="field" id="category_pack_version_id" name="category_pack_version_id" required>
              {categoryPacks.map((pack) => <option key={pack.version_id} value={pack.version_id}>{pack.name} · v{pack.version}</option>)}
            </select>
          </div>
          <div>
            <label className="field-label mb-2" htmlFor="brand_pack_version_id">品牌视觉</label>
            <select className="field" id="brand_pack_version_id" name="brand_pack_version_id" required>
              {brandPacks.map((pack) => <option key={pack.version_id} value={pack.version_id}>{pack.name} · v{pack.version}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className="field-label mb-2" htmlFor="mode">真实性模式</label>
          <select className="field" id="mode" name="mode" defaultValue="strict">
            <option value="strict">严格商品模式（缺少必要参考图时阻止编译）</option>
            <option value="creative">创意模式（允许 AI 补全，结果仍需人工审核）</option>
          </select>
        </div>
        <p className="text-xs leading-5 text-slate-500">平台规则为中台维护的可追溯默认值，不代表平台官方认证。正式上架前仍应按目标站点最新政策复核。</p>
        <button className="primary-button min-h-11" disabled={busy !== null || !products.length || !packs.length}>
          {busy === "compile" ? "正在编译…" : "编译图片套装"}
        </button>
      </form>

      {plan && <PlanPreview plan={plan} models={eligibleModels} onChange={setPlan} />}
      {plan && (
        <div className="mt-5 grid gap-4 md:grid-cols-[1fr_auto]">
          <div>
            <label className="field-label mb-2" htmlFor="model_configuration_id">生图模型</label>
            <select className="field" id="model_configuration_id" value={modelId} onChange={(event) => setModelId(event.target.value)}>
              {eligibleModels.map((model) => <option key={model.id} value={model.id}>{model.name} · {model.model_id}</option>)}
            </select>
          </div>
          <button type="button" className="primary-button min-h-11 self-end" disabled={busy !== null || !modelId} onClick={execute}>
            {busy === "execute" ? "正在创建任务…" : "开始生成套图"}
          </button>
        </div>
      )}
      <p className="mt-4 min-h-5 text-sm text-slate-400" role="status" aria-live="polite">{message}</p>
    </div>
  );
}
