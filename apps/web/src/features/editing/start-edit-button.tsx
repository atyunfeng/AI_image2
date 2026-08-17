"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function StartEditButton({ batchId, disabled }: { batchId: string; disabled: boolean }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function start() {
    setBusy(true);
    setMessage("");
    const response = await fetch("/api/backend/edit-projects", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ source_batch_id: batchId }) });
    if (response.ok) { const project = await response.json(); router.push(`/editing/${project.id}`); return; }
    setMessage("无法创建编辑项目，请确认图片已经生成完成。");
    setBusy(false);
  }
  return <div className="mt-4"><button className="secondary-button min-h-11 w-full" type="button" disabled={disabled || busy} onClick={start}>{busy ? "正在创建编辑分支…" : "微调此图"}</button><p className="mt-2 min-h-4 text-xs text-red-300" role="status">{message}</p></div>;
}
