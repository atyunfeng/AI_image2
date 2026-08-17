import { ProductionForm } from "@/features/templates/production-form";
import { safeApiFetch } from "@/lib/api-client";
import { ModelConfiguration, Product, TemplatePack } from "@/lib/types";

export default async function NewProductionPage() {
  const [products, models, packs] = await Promise.all([
    safeApiFetch<Product[]>("/products", []),
    safeApiFetch<ModelConfiguration[]>("/models", []),
    safeApiFetch<TemplatePack[]>("/template-packs", []),
  ]);
  const ready = products.length > 0 && models.some((model) => model.is_enabled) && packs.length > 0;
  return (
    <div className="mx-auto max-w-5xl space-y-7">
      <div>
        <p className="eyebrow">PLATFORM IMAGE SET</p>
        <h1 className="page-title">电商套图生产</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">选择商品和目标平台，先编译可核对的图片清单，再创建每张独立可恢复的生成任务。</p>
      </div>
      {ready ? <section className="panel p-6 md:p-8"><ProductionForm products={products} models={models} packs={packs} /></section> : <p className="empty-copy">请先创建商品、上传正面参考图并配置可用生图模型。</p>}
    </div>
  );
}
