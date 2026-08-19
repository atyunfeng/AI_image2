"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { ModelConfiguration } from "@/lib/types";

const capabilityOptions = [
  ["reference_to_image", "商品图 / 详情图"],
  ["multi_reference_to_image", "模特多角度"],
  ["virtual_try_on", "虚拟试穿"],
  ["inpaint", "局部重绘 / 消除"],
  ["outpaint", "扩图"],
  ["remove_background", "自动抠背景"],
] as const;

export function ModelList({ models }: { models: ModelConfiguration[] }) {
  if (!models.length) return <p className="empty-copy">还没有模型配置。</p>;
  return <div className="space-y-3">{models.map((model) => <ModelRow model={model} key={model.id} />)}</div>;
}

function ModelRow({ model }: { model: ModelConfiguration }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function update(payload: Record<string, unknown>) {
    setBusy(true);
    setMessage("");
    const response = await fetch(`/api/backend/models/${model.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json().catch(() => ({}));
    setBusy(false);
    setMessage(response.ok ? "配置已更新" : body.detail ?? "更新失败，请检查权限和参数");
    if (response.ok) router.refresh();
  }

  async function testConnection() {
    setBusy(true);
    setMessage("正在测试连接…");
    const response = await fetch(`/api/backend/models/${model.id}/test`, { method: "POST" });
    setBusy(false);
    setMessage(response.ok ? "连接成功，结果已写入审计" : "连接失败，请检查地址、密钥和网络策略");
  }

  function rotate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const apiKey = String(data.get("api_key") || "");
    if (!apiKey) return setMessage("请输入新 API KEY");
    void update({ api_key: apiKey }).then(() => form.reset());
  }

  function edit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    let providerOptions: Record<string, unknown>;
    try {
      providerOptions = JSON.parse(String(data.get("provider_options") || "{}"));
    } catch {
      setMessage("Provider 参数必须是有效 JSON");
      return;
    }
    const capabilities = capabilityOptions
      .map(([value]) => value)
      .filter((value) => data.get(value) === "on");
    if (!capabilities.length) {
      setMessage("至少保留一项模型能力");
      return;
    }
    void update({
      name: data.get("name"),
      model_id: data.get("model_id"),
      base_url: data.get("base_url") || null,
      billing_currency: String(data.get("billing_currency") || "USD").toUpperCase(),
      provider_options: providerOptions,
      capabilities,
    });
  }

  return (
    <article className="rounded-2xl border border-white/8 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0"><p className="truncate font-semibold" title={model.name}>{model.name}</p><p className="mt-1 break-all text-xs text-slate-500">{model.provider} / {model.model_id} · {model.billing_currency}</p>{model.has_key && <span className="mt-1 block text-xs text-slate-400">••••{model.key_suffix}</span>}</div>
        <span className={model.is_enabled ? "status-pill" : "failure-pill"}>{model.is_enabled ? "可用" : "停用"}</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <button className="secondary-button min-h-11" type="button" disabled={busy} onClick={testConnection}>测试连接</button>
        <button className="secondary-button min-h-11" type="button" disabled={busy} onClick={() => update({ is_enabled: !model.is_enabled })}>{model.is_enabled ? "停用" : "启用"}</button>
      </div>
      <details className="mt-4">
        <summary className="cursor-pointer text-sm text-orange-200">编辑连接与能力</summary>
        <form className="form-grid mt-3" onSubmit={edit}>
          <div className="grid gap-3 sm:grid-cols-2"><div><label className="field-label mb-2" htmlFor={`model-name-${model.id}`}>名称（编辑现有项）</label><input className="field" id={`model-name-${model.id}`} name="name" defaultValue={model.name} required /></div><div><label className="field-label mb-2" htmlFor={`model-id-${model.id}`}>标识（编辑现有项）</label><input className="field" id={`model-id-${model.id}`} name="model_id" defaultValue={model.model_id} required /></div></div>
          <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_110px]"><div><label className="field-label mb-2" htmlFor={`model-url-${model.id}`}>连接地址（编辑）</label><input className="field" id={`model-url-${model.id}`} name="base_url" defaultValue={model.base_url ?? ""} /></div><div><label className="field-label mb-2" htmlFor={`model-currency-${model.id}`}>币种（编辑）</label><input className="field uppercase" id={`model-currency-${model.id}`} name="billing_currency" defaultValue={model.billing_currency} pattern="[A-Za-z]{3}" maxLength={3} required /></div></div>
          <div><label className="field-label mb-2" htmlFor={`model-options-${model.id}`}>参数 JSON（编辑）</label><textarea className="field min-h-32 font-mono text-xs" id={`model-options-${model.id}`} name="provider_options" defaultValue={JSON.stringify(model.provider_options, null, 2)} /></div>
          <fieldset className="rounded-xl border border-white/10 p-4"><legend className="px-2 text-xs font-semibold text-slate-300">编辑已有能力</legend><div className="grid gap-2 sm:grid-cols-2">{capabilityOptions.map(([value, label]) => <label className="flex min-h-11 items-center gap-3 text-sm text-slate-300" key={value}><input type="checkbox" name={value} aria-label={`切换已配置能力 ${value}`} defaultChecked={model.capabilities.includes(value)} /><span>{label}</span></label>)}</div></fieldset>
          <button className="primary-button min-h-11" disabled={busy}>保存连接配置</button>
        </form>
      </details>
      <details className="mt-4">
        <summary className="cursor-pointer text-sm text-orange-200">轮换 API KEY</summary>
        <form className="mt-3 flex flex-col gap-3 sm:flex-row" onSubmit={rotate}>
          <div className="min-w-0 flex-1"><label className="sr-only" htmlFor={`model-key-${model.id}`}>新的 API KEY</label><input className="field" id={`model-key-${model.id}`} name="api_key" type="password" autoComplete="new-password" placeholder={model.has_key ? `当前 ••••${model.key_suffix}` : "输入新的 API KEY"} /></div>
          <button className="primary-button min-h-11" disabled={busy}>保存新密钥</button>
        </form>
      </details>
      <p className="mt-3 min-h-5 text-xs text-slate-400" role="status" aria-live="polite">{message}</p>
    </article>
  );
}
