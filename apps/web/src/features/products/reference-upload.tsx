"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
export function ReferenceUpload({ productId }: { productId: string }) {
  const router = useRouter();
  const [message, setMessage] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const response = await fetch(
      `/api/backend/products/${productId}/references`,
      { method: "POST", body: data },
    );
    setMessage(response.ok ? "参考图已固化" : "上传失败");
    if (response.ok) {
      form.reset();
      router.refresh();
    }
  }
  return (
    <form onSubmit={submit} className="form-grid">
      <select className="field" name="view">
        <option value="front">正面</option>
        <option value="side">侧面</option>
        <option value="back">背面</option>
        <option value="detail">细节</option>
        <option value="logo">Logo</option>
      </select>
      <input
        className="field"
        name="file"
        type="file"
        accept="image/png,image/jpeg,image/webp"
        required
      />
      <button className="secondary-button">上传参考图</button>
      {message && <p className="text-xs text-slate-400">{message}</p>}
    </form>
  );
}
