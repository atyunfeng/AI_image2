"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { ModelConfiguration } from "@/lib/types";

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
    setBusy(false);
    setMessage(response.ok ? "配置已更新" : "更新失败，请检查权限和参数");
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
