/* eslint-disable @next/next/no-img-element */
import { ProductManagement } from "@/features/products/product-management";
import { ReferenceUpload } from "@/features/products/reference-upload";
import { safeApiFetch } from "@/lib/api-client";
import { Product } from "@/lib/types";

export default async function ProductDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const product = await safeApiFetch<Product | null>(`/products/${id}`, null);
  if (!product) return <p className="empty-copy">商品不存在、已归档或服务暂不可用。</p>;
  const metrics = product.history ?? { generations: 0, edits: 0, reviews: 0, exports: 0 };
  const labels = { generations: "生成", edits: "微调", reviews: "审核", exports: "导出" };
  return <div className="space-y-7"><div><p className="eyebrow">{product.sku} · {product.brand || "未设置品牌"}</p><h1 className="page-title">{product.name}</h1></div>
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{Object.entries(metrics).map(([key, value]) => <div className="metric-card" key={key}><span>{labels[key as keyof typeof labels]}</span><strong>{value}</strong></div>)}</div>
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]"><div className="space-y-6"><section className="panel p-6"><h2 className="section-title mb-5">不可变参考图</h2>{product.references?.length ? <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{product.references.map((ref) => <div key={ref.id} className="overflow-hidden rounded-xl border border-white/10"><img src={`/api/backend/assets/${ref.asset_id}/content`} alt={`${ref.view}参考图`} className="aspect-square w-full bg-white object-contain" /><p className="p-3 text-xs text-slate-400">{ref.view} · {ref.sha256.slice(0, 10)}</p></div>)}</div> : <p className="empty-copy">至少上传一张正面图后再生成。</p>}</section><section className="panel p-6"><h2 className="section-title mb-5">新增视角</h2><ReferenceUpload productId={id} /></section></div><ProductManagement product={product} /></div>
  </div>;
}
