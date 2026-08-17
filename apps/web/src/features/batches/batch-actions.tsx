"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Batch } from "@/lib/types";

export function BatchActions({ batch }: { batch: Batch }) {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function retry() {
    setBusy(true);
    const response = await fetch(`/api/backend/batches/${batch.id}/retry`, { method: "POST" });
    const body = await response.json().catch(() => ({ detail: "重试失败" }));
    if (response.ok) router.push(`/batches/${body.id}`); else setMessage(body.detail ?? "重试失败");
    setBusy(false);
  }

  async function duplicate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const form = new FormData(event.currentTarget);
    const response = await fetch(`/api/backend/batches/${batch.id}/duplicate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: form.get("prompt"), width: Number(form.get("width")), height: Number(form.get("height")) }),
    });
    const body = await response.json().catch(() => ({ detail: "复制失败" }));
    if (response.ok) router.push(`/batches/${body.id}`); else setMessage(body.detail ?? "复制失败");
    setBusy(false);
  }

  const retryable = ["failed", "rejected", "canceled"].includes(batch.status);
  return <section className="panel p-6"><div className="flex items-center justify-between gap-3"><div><p className="eyebrow">PROVENANCE</p><h2 className="section-title mt-2">重试与参数复制</h2></div>{batch.source_batch_id && <span className="version-chip">源 {batch.source_batch_id.slice(0, 8)}</span>}</div><form className="form-grid mt-5" onSubmit={duplicate}><div><label className="field-label mb-2" htmlFor="duplicate-prompt">提示词</label><textarea className="field min-h-24" id="duplicate-prompt" name="prompt" defaultValue={batch.prompt} required /></div><div className="grid grid-cols-2 gap-3"><div><label className="field-label mb-2" htmlFor="duplicate-width">宽</label><input className="field" id="duplicate-width" name="width" type="number" min="64" max="4096" defaultValue={batch.width} required /></div><div><label className="field-label mb-2" htmlFor="duplicate-height">高</label><input className="field" id="duplicate-height" name="height" type="number" min="64" max="4096" defaultValue={batch.height} required /></div></div><button className="secondary-button" disabled={busy}>复制为新批次</button></form><button className="primary-button mt-3 w-full" type="button" onClick={retry} disabled={busy || !retryable}>按原参数重试</button><p className="mt-3 min-h-5 text-xs text-orange-200" role="status">{message || (!retryable ? "仅失败、驳回或取消的批次可原样重试。" : "")}</p></section>;
}
