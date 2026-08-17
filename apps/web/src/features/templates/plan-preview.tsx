import { ProductionPlan } from "@/lib/types";

export function PlanPreview({ plan }: { plan: ProductionPlan }) {
  return (
    <section aria-labelledby="plan-preview-title" className="mt-6 rounded-2xl border border-orange-300/20 bg-orange-300/[0.04] p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="eyebrow">COMPILED PLAN</p>
          <h2 id="plan-preview-title" className="section-title mt-2">已编译 {plan.items.length} 张图片</h2>
        </div>
        <span className="version-chip">规则哈希 {plan.compiler_hash.slice(0, 10)}</span>
      </div>
      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {plan.items.map((item) => (
          <article className="plan-slot" key={item.id}>
            <p className="text-sm font-semibold text-slate-100">{item.label}</p>
            <p className="mt-1 text-xs text-slate-400">{item.width} × {item.height} · {item.requested_view}</p>
            <p className="mt-3 text-xs text-slate-500">{item.authoritative_copy ? `确定性文字：${item.authoritative_copy}` : "无文字底图"}</p>
          </article>
        ))}
      </div>
      <div className="mt-5 flex flex-wrap gap-2">
        {Object.entries(plan.compiled_snapshot.packs).map(([kind, pack]) => (
          <span className="version-chip" key={kind}>{kind} · {pack.slug} v{pack.version}</span>
        ))}
      </div>
    </section>
  );
}
