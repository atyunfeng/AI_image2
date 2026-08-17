"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { FashionOutput, ModelConfiguration, ModelProfile, Product } from "@/lib/types";

const outputs: { value: FashionOutput; label: string; help: string; capability: string }[] = [
  { value: "product_front", label: "商品正面图", help: "保留材质、颜色、Logo 与版型", capability: "reference_to_image" },
  { value: "model_front", label: "模特正面图", help: "商品与模特参考联合生成", capability: "multi_reference_to_image" },
  { value: "model_side", label: "模特侧面图", help: "严格模式需要商品侧面参考图", capability: "multi_reference_to_image" },
  { value: "model_back", label: "模特背面图", help: "严格模式需要商品背面参考图", capability: "multi_reference_to_image" },
  { value: "detail", label: "商品细节图", help: "强调材质、工艺与局部结构", capability: "reference_to_image" },
  { value: "virtual_try_on", label: "虚拟试穿图", help: "检查人体结构、穿插与商品一致性", capability: "virtual_try_on" },
];

type Props = { products: Product[]; profiles: ModelProfile[]; models: ModelConfiguration[] };

export function FashionForm({ products, profiles, models }: Props) {
  const router = useRouter();
  const [selectedOutputs, setSelectedOutputs] = useState<FashionOutput[]>(["product_front", "model_front", "virtual_try_on"]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const requiredCapabilities = useMemo(() => new Set(outputs.filter((output) => selectedOutputs.includes(output.value)).map((output) => output.capability)), [selectedOutputs]);
  const eligibleModels = models.filter((model) => model.is_enabled && [...requiredCapabilities].every((capability) => model.capabilities.includes(capability)));
  const selectableProfiles = profiles.filter((profile) => profile.is_selectable);
  const fashionProducts = products.filter((product) => product.category !== "other");

  function toggleOutput(value: FashionOutput) {
    setSelectedOutputs((current) => current.includes(value) ? current.filter((item) => item !== value) : [...current, value]);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedOutputs.length) { setMessage("请至少选择一种输出图片。"); return; }
    setBusy(true);
    setMessage("");
    const data = new FormData(event.currentTarget);
    const response = await fetch("/api/backend/fashion-plans", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_id: data.get("product_id"),
        model_profile_id: data.get("model_profile_id"),
        model_configuration_id: data.get("model_configuration_id"),
        requested_outputs: selectedOutputs,
        mode: data.get("mode"),
      }),
    });
    if (response.ok) {
      const plan = await response.json();
      router.push(`/fashion/${plan.id}`);
      router.refresh();
      return;
    }
    const body = await response.json().catch(() => ({ detail: "创建失败" }));
    setMessage(body.detail ?? "创建失败，请检查商品和模特参考视角。");
    setBusy(false);
  }

  return <form className="form-grid" onSubmit={submit} aria-busy={busy}><div className="grid gap-4 md:grid-cols-3"><div><label className="field-label mb-2" htmlFor="fashion-product">服装 / 鞋 / 帽商品</label><select className="field" id="fashion-product" name="product_id" required>{fashionProducts.map((product) => <option value={product.id} key={product.id}>{product.sku} · {product.name}</option>)}</select></div><div><label className="field-label mb-2" htmlFor="fashion-profile">授权模特</label><select className="field" id="fashion-profile" name="model_profile_id" required>{selectableProfiles.map((profile) => <option value={profile.id} key={profile.id}>{profile.name} · {profile.references.length} 个视角</option>)}</select></div><div><label className="field-label mb-2" htmlFor="fashion-model">生图模型</label><select className="field" id="fashion-model" name="model_configuration_id" required>{eligibleModels.map((model) => <option value={model.id} key={model.id}>{model.name} · {model.model_id}</option>)}</select></div></div><fieldset><legend className="field-label mb-3">输出图片</legend><div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{outputs.map((output) => { const checked = selectedOutputs.includes(output.value); return <label className={`output-option ${checked ? "output-option-selected" : ""}`} key={output.value}><input type="checkbox" checked={checked} onChange={() => toggleOutput(output.value)} /><span><strong>{output.label}</strong><small>{output.help}</small></span></label>; })}</div></fieldset><div><label className="field-label mb-2" htmlFor="fashion-mode">真实性模式</label><select className="field" id="fashion-mode" name="mode" defaultValue="strict"><option value="strict">严格商品模式（缺少对应商品视角时阻止创建）</option><option value="creative">创意补全模式（明确标记推断视角并强制人工审核）</option></select></div>{!eligibleModels.length && <p className="failure-note">当前没有同时支持所选能力的模型，请先到“模型”页面勾选商品图、多角度与虚拟试穿能力。</p>}<button className="primary-button min-h-11" disabled={busy || !fashionProducts.length || !selectableProfiles.length || !eligibleModels.length}>{busy ? "正在编译并创建任务…" : `开始生成 ${selectedOutputs.length} 张图片`}</button><p className="min-h-5 text-sm text-red-300" role="status" aria-live="polite">{message}</p></form>;
}
