"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export function ProfileForm() {
  const router = useRouter();
  const [profileType, setProfileType] = useState("system_virtual");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    const data = new FormData(event.currentTarget);
    const brandAuthorized = profileType === "brand_authorized";
    const response = await fetch("/api/backend/model-profiles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: data.get("name"),
        profile_type: profileType,
        authorization_status: brandAuthorized ? "valid" : "not_required",
        authorization_expires_on: brandAuthorized ? data.get("authorization_expires_on") || null : null,
        attributes: {
          gender_presentation: data.get("gender_presentation") || null,
          market: data.get("market") || null,
        },
      }),
    });
    if (response.ok) {
      const profile = await response.json();
      router.push(`/talent/${profile.id}`);
      router.refresh();
      return;
    }
    const body = await response.json().catch(() => ({ detail: "创建失败" }));
    setMessage(body.detail ?? "创建失败，请检查授权有效期。");
    setBusy(false);
  }

  return (
    <form className="form-grid" onSubmit={submit} aria-busy={busy}>
      <div>
        <label className="field-label mb-2" htmlFor="profile-name">模特名称</label>
        <input className="field" id="profile-name" name="name" required />
      </div>
      <div>
        <label className="field-label mb-2" htmlFor="profile-type">资产类型</label>
        <select className="field" id="profile-type" name="profile_type" value={profileType} onChange={(event) => setProfileType(event.target.value)}>
          <option value="system_virtual">系统虚拟模特</option>
          <option value="brand_authorized">品牌授权模特</option>
        </select>
      </div>
      {profileType === "brand_authorized" && <div>
        <label className="field-label mb-2" htmlFor="authorization-expires-on">授权有效期</label>
        <input className="field" id="authorization-expires-on" name="authorization_expires_on" type="date" required />
        <p className="mt-2 text-xs text-slate-500">到期后中台会阻止新任务和执行中的任务继续使用该模特。</p>
      </div>}
      <div className="grid gap-4 sm:grid-cols-2">
        <div><label className="field-label mb-2" htmlFor="gender-presentation">形象标签</label><input className="field" id="gender-presentation" name="gender_presentation" placeholder="例如：中性 / 女装 / 男装" /></div>
        <div><label className="field-label mb-2" htmlFor="market">适用市场</label><input className="field" id="market" name="market" placeholder="例如：中国 / 北美 / 全球" /></div>
      </div>
      <button className="primary-button min-h-11" disabled={busy}>{busy ? "创建中…" : "创建并上传参考图"}</button>
      <p className="min-h-5 text-sm text-red-300" role="status" aria-live="polite">{message}</p>
    </form>
  );
}
