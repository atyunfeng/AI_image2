"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

const capabilities = [
  ["reference_to_image", "商品图 / 详情图"],
  ["multi_reference_to_image", "模特多角度"],
  ["virtual_try_on", "虚拟试穿"],
  ["inpaint", "局部重绘 / 消除"],
  ["outpaint", "扩图"],
  ["remove_background", "自动抠背景"],
] as const;

const comfyExample = JSON.stringify({
  workflow: { "6": { inputs: { text: "" }, class_type: "CLIPTextEncode" } },
  bindings: { prompt: ["6", "inputs", "text"] },
  reference_bindings: [],
  output_node_id: "9",
  timeout_seconds: 180,
  cost_minor: 0,
}, null, 2);

export function ModelForm() {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [provider, setProvider] = useState("mock");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    const form = event.currentTarget;
    const data = new FormData(form);
    const selected = capabilities.map(([value]) => value).filter((value) => data.get(value) === "on");
    let providerOptions: Record<string, unknown> = {};
    if (provider === "comfyui") {
      try {
        providerOptions = JSON.parse(String(data.get("provider_options") || "{}"));
      } catch {
        setMessage("ComfyUI 工作流参数必须是有效 JSON");
        setBusy(false);
        return;
      }
    }
    const response = await fetch("/api/backend/models", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: data.get("name"), provider, model_id: data.get("model_id"),
        base_url: data.get("base_url") || null, api_key: data.get("api_key") || null,
        billing_currency: data.get("billing_currency"), provider_options: providerOptions,
        capabilities: selected,
      }),
    });
    if (response.ok) {
      form.reset();
      setProvider("mock");
      setMessage("模型配置已保存，密钥不会再次显示");
      router.refresh();
    } else setMessage("保存失败，请检查配置和至少一项模型能力");
    setBusy(false);
  }

  return <form onSubmit={submit} className="form-grid" aria-busy={busy}>
    <div><label className="field-label mb-2" htmlFor="model-name">配置名称</label><input className="field" id="model-name" name="name" required /></div>
    <div><label className="field-label mb-2" htmlFor="provider">服务类型</label><select className="field" id="provider" name="provider" value={provider} onChange={(event) => setProvider(event.target.value)}><option value="mock">Mock（本地验收）</option><option value="generic_http">通用 HTTP API</option><option value="comfyui">本地 ComfyUI 节点</option></select></div>
    <div><label className="field-label mb-2" htmlFor="model-id">模型 ID / 工作流名</label><input className="field" id="model-id" name="model_id" required /></div>
    <div className="grid grid-cols-[1fr_110px] gap-3"><div><label className="field-label mb-2" htmlFor="base-url">API Base URL</label><input className="field" id="base-url" name="base_url" placeholder={provider === "comfyui" ? "http://host.docker.internal:8188" : "Mock 可留空"} /></div><div><label className="field-label mb-2" htmlFor="billing-currency">成本币种</label><input className="field uppercase" id="billing-currency" name="billing_currency" defaultValue="USD" pattern="[A-Za-z]{3}" maxLength={3} required /></div></div>
    <div><label className="field-label mb-2" htmlFor="api-key">API KEY</label><input className="field" id="api-key" name="api_key" type="password" autoComplete="new-password" placeholder={provider === "comfyui" ? "本地节点无鉴权可留空" : "加密保存"} /></div>
    {provider === "comfyui" && <div><label className="field-label mb-2" htmlFor="provider-options">ComfyUI 工作流参数</label><textarea className="field min-h-64 font-mono text-xs" id="provider-options" name="provider_options" defaultValue={comfyExample} /><p className="mt-2 text-xs leading-5 text-slate-500">粘贴 API format 工作流，并用 bindings 指定提示词、尺寸、参考图和输出节点。工作流不含 API KEY。</p></div>}
    <fieldset className="rounded-xl border border-white/10 p-4"><legend className="px-2 text-xs font-semibold text-slate-300">模型能力</legend><div className="grid gap-3">{capabilities.map(([value, label], index) => <label className="flex min-h-11 cursor-pointer items-center gap-3 text-sm text-slate-300" key={value}><input type="checkbox" name={value} defaultChecked={index === 0} /><span>{label}</span></label>)}</div></fieldset>
    <button className="primary-button" disabled={busy}>{busy ? "保存中…" : "保存模型"}</button>
    <p className="min-h-5 text-xs text-slate-400" role="status" aria-live="polite">{message}</p>
  </form>;
}
