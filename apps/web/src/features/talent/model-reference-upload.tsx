"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export function ModelReferenceUpload({ profileId }: { profileId: string }) {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const form = event.currentTarget;
    const response = await fetch(`/api/backend/model-profiles/${profileId}/references`, { method: "POST", body: new FormData(form) });
    setMessage(response.ok ? "参考视角已固化" : "上传失败，请使用 PNG、JPEG 或 WebP 图片");
    if (response.ok) { form.reset(); router.refresh(); }
    setBusy(false);
  }
  return <form className="form-grid" onSubmit={submit} aria-busy={busy}><div><label className="field-label mb-2" htmlFor="model-view">参考视角</label><select className="field" id="model-view" name="view"><option value="front">正面</option><option value="side">侧面</option><option value="back">背面</option><option value="half_body">半身</option><option value="full_body">全身</option></select></div><div><label className="field-label mb-2" htmlFor="model-reference-file">图片文件</label><input className="field" id="model-reference-file" name="file" type="file" accept="image/png,image/jpeg,image/webp" required /></div><button className="secondary-button min-h-11" disabled={busy}>{busy ? "上传中…" : "上传参考图"}</button><p className="min-h-5 text-xs text-slate-400" role="status" aria-live="polite">{message}</p></form>;
}
