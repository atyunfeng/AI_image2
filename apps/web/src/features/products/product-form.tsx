"use client";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { z } from "zod";

const schema = z.object({ sku: z.string().trim().min(1, "请输入SKU"), name: z.string().trim().min(1, "请输入商品名称"), brand: z.string().trim().optional(), category: z.enum(["apparel", "shoes", "hats", "other"]) });

export function ProductForm({ onSubmit }: { onSubmit?: (value: z.infer<typeof schema>) => Promise<void> | void }) {
  const router = useRouter(); const [errors,setErrors]=useState<string[]>([]); const [pending,setPending]=useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const form=new FormData(event.currentTarget); const parsed=schema.safeParse({sku:form.get("sku"),name:form.get("name"),brand:form.get("brand"),category:form.get("category")}); if(!parsed.success){setErrors(parsed.error.issues.map(i=>i.message));return;} setPending(true); if(onSubmit){await onSubmit(parsed.data);}else{const response=await fetch("/api/backend/products",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(parsed.data)});if(response.ok){const product=await response.json();router.push(`/products/${product.id}`);router.refresh();}else setErrors(["创建失败，请检查 SKU 是否重复"]);} setPending(false); }
  return <form onSubmit={submit} className="form-grid"><div><label className="field-label mb-2" htmlFor="sku">SKU</label><input className="field" id="sku" name="sku" required /></div><div><label className="field-label mb-2" htmlFor="name">商品名称</label><input className="field" id="name" name="name" required /></div><div><label className="field-label mb-2" htmlFor="brand">品牌</label><input className="field" id="brand" name="brand" autoComplete="organization" /></div><div><label className="field-label mb-2" htmlFor="category">品类</label><select className="field" id="category" name="category" defaultValue="apparel"><option value="apparel">服装</option><option value="shoes">鞋靴</option><option value="hats">帽饰</option><option value="other">其他</option></select></div>{errors.map(error=><p className="text-sm text-red-400" key={error}>{error}</p>)}<button className="primary-button" disabled={pending}>{pending?"创建中…":"创建商品"}</button></form>;
}
