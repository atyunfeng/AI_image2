"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Batch } from "@/lib/types";

export function ReviewPanel({ batch, onDecision }: { batch: Batch; onDecision?: (decision: "approve" | "reject") => void }) {
  const router = useRouter();
  const [reason, setReason] = useState("product_drift");
  const [note, setNote] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const ready = batch.status === "review_pending";
  const canExport = ["approved", "exported"].includes(batch.status);
  async function decide(decision: "approve" | "reject") {
    onDecision?.(decision);
    if (onDecision) return;
    setBusy(true);
    const response = await fetch(`/api/backend/batches/${batch.id}/review`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ decision, rejection_reason: decision === "reject" ? reason : null, note: note || null }) });
    setMessage(response.ok ? "审核结果已记录" : response.status === 403 ? "当前账户没有审核权限" : "审核失败，请重试");
    setBusy(false);
    if (response.ok) router.refresh();
  }
  return <section className="panel p-6" aria-busy={busy}><h2 className="section-title">人工审核</h2><p className="mt-2 text-sm text-slate-400">确认商品身份、颜色材质、文字与平台规范后再放行。</p><div className="mt-5 form-grid"><div><label className="field-label mb-2" htmlFor="review-reason">驳回原因</label><select id="review-reason" className="field" value={reason} onChange={(event) => setReason(event.target.value)}><option value="product_drift">商品漂移</option><option value="color_error">颜色错误</option><option value="text_error">文字错误</option><option value="model_anatomy">模特肢体异常</option><option value="platform_rule">平台规则</option><option value="other">其他</option></select></div><div><label className="field-label mb-2" htmlFor="review-note">审核备注</label><textarea id="review-note" className="field" placeholder="记录判断依据；选择“其他”时必填" value={note} onChange={(event) => setNote(event.target.value)} /></div><div className="grid gap-3 sm:grid-cols-3"><button className="primary-button" type="button" disabled={!ready || busy} onClick={() => decide("approve")}>通过</button><button className="secondary-button" type="button" disabled={!ready || busy || (reason === "other" && !note.trim())} onClick={() => decide("reject")}>驳回</button>{canExport ? <a className="secondary-button" href={`/api/backend/batches/${batch.id}/export.zip`}>导出</a> : <button className="secondary-button" type="button" disabled>导出</button>}</div><p className="min-h-5 text-xs text-slate-400" role="status" aria-live="polite">{message}</p></div></section>;
}
