import Link from "next/link";

import { FashionForm } from "@/features/fashion/fashion-form";
import { safeApiFetch } from "@/lib/api-client";
import { ModelConfiguration, ModelProfile, Product } from "@/lib/types";

export default async function NewFashionPage() {
  const [products, profiles, models] = await Promise.all([safeApiFetch<Product[]>("/products", []), safeApiFetch<ModelProfile[]>("/model-profiles", []), safeApiFetch<ModelConfiguration[]>("/models", [])]);
  const ready = products.some((product) => product.category !== "other") && profiles.some((profile) => profile.is_selectable) && models.some((model) => model.is_enabled);
  return <div className="mx-auto max-w-6xl space-y-7"><div><p className="eyebrow">FASHION WORKFLOW</p><h1 className="page-title">多角度与虚拟试穿</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">一次选择商品、授权模特和输出清单，中台按能力拆分任务。严格模式不允许凭空生成缺失的商品侧面或背面结构。</p></div>{ready ? <section className="panel p-6 md:p-8"><FashionForm products={products} profiles={profiles} models={models} /></section> : <section className="empty-copy"><p>还缺少可用的服饰商品、已上传参考图的模特，或生图模型配置。</p><div className="mt-5 flex flex-wrap justify-center gap-3"><Link className="secondary-button" href="/products/new">新建商品</Link><Link className="secondary-button" href="/talent/new">新建模特</Link><Link className="secondary-button" href="/models">配置模型</Link></div></section>}</div>;
}
