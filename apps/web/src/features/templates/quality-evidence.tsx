import { QualityRun } from "@/lib/types";

export function QualityEvidence({ quality }: { quality: QualityRun | null }) {
  if (!quality) return <p className="mt-4 text-xs text-slate-500">等待结构质检证据…</p>;
  return (
    <div className="mt-4 rounded-xl border border-white/10 bg-black/10 p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold">结构质检</p>
        <span className={quality.passed ? "status-pill" : "failure-pill"}>{quality.passed ? "通过" : "阻断"}</span>
      </div>
      <ul className="mt-3 space-y-2">
        {quality.checks.map((check) => (
          <li className="flex items-start gap-2 text-xs text-slate-400" key={check.code}>
            <span aria-hidden="true" className={check.passed ? "text-emerald-300" : "text-red-300"}>{check.passed ? "●" : "×"}</span>
            <span><span className="text-slate-200">{check.code}</span> · {check.message}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
