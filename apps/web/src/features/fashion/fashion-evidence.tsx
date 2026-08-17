import { FashionEvidence } from "@/lib/types";

const checkLabels: Record<string, string> = { authorization_current: "模特授权当前有效", required_product_views: "商品参考视角满足要求", required_model_views: "模特参考视角满足要求", output_dimensions: "输出尺寸符合计划", inferred_view_labeled: "推断视角已明确标记" };
const reviewLabels: Record<string, string> = { model_identity: "模特身份一致性", anatomy: "人体结构", garment_penetration: "服饰穿插", product_structure: "商品结构", cross_view_consistency: "跨视角一致性" };

export function FashionEvidenceCard({ evidence }: { evidence: FashionEvidence | null }) {
  if (!evidence) return <p className="mt-4 text-xs text-slate-500">等待服饰质检证据…</p>;
  return <div className="mt-4 rounded-xl border border-white/10 bg-black/10 p-4"><div className="flex items-center justify-between gap-3"><p className="text-sm font-semibold">服饰质检</p><span className={evidence.automated_passed ? "status-pill" : "failure-pill"}>{evidence.automated_passed ? "自动项通过" : "自动项阻断"}</span></div><ul className="mt-3 space-y-2">{Object.entries(evidence.checks).map(([code, passed]) => <li className="flex items-start gap-2 text-xs text-slate-400" key={code}><span aria-hidden="true" className={passed ? "text-emerald-300" : "text-red-300"}>{passed ? "●" : "×"}</span><span>{checkLabels[code] ?? code}</span></li>)}</ul><div className="mt-4 border-t border-white/10 pt-3"><p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">必须人工复核</p><p className="mt-2 text-xs leading-5 text-slate-400">{evidence.human_review_checks.map((item) => reviewLabels[item] ?? item).join("、")}</p></div></div>;
}
