"use client";
/* eslint-disable @next/next/no-img-element */

import { useState } from "react";

export function SelectionManager({ projectId, revisionId }: { projectId: string; revisionId: string }) {
  const [maskAssetId, setMaskAssetId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function select(selectionType: "foreground" | "background" | "person" | "garment") {
    setBusy(true);
    const response = await fetch(`/api/backend/edit-projects/${projectId}/selections`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ revision_id: revisionId, selection_type: selectionType, threshold: 42 }),
    });
    const body = await response.json().catch(() => ({ detail: "自动选择失败" }));
    if (response.ok) {
      setMaskAssetId(body.mask_asset_id);
      setMessage(`${selectionType} 蒙版已生成并作为不可变资产保存。`);
    } else setMessage(body.detail ?? "自动选择失败");
    setBusy(false);
  }

  return <section className="panel p-5"><div><p className="eyebrow">AUTO SELECTION</p><h2 className="section-title mt-2">自动选择蒙版</h2></div><div className="mt-5 flex flex-wrap gap-2"><button className="secondary-button" type="button" disabled={busy} onClick={() => select("foreground")}>商品主体</button><button className="secondary-button" type="button" disabled={busy} onClick={() => select("background")}>背景</button><button className="secondary-button" type="button" disabled={busy} onClick={() => select("person")}>人物</button><button className="secondary-button" type="button" disabled={busy} onClick={() => select("garment")}>服装</button></div>{maskAssetId && <a className="mt-4 block w-fit" href={`/api/backend/assets/${maskAssetId}/content`} target="_blank"><img className="h-32 w-32 rounded-xl border border-white/10 bg-black object-contain" src={`/api/backend/assets/${maskAssetId}/content`} alt="自动选择蒙版" /></a>}<p className="mt-3 min-h-5 text-xs text-orange-200" role="status">{message}</p></section>;
}
