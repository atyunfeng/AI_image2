import { safeApiFetch } from "@/lib/api-client";
import { CostReport } from "@/lib/types";

const emptyReport: CostReport = { generated_at: "", cost_basis: "provider_reported_or_estimated", summaries: [], daily: [], breakdown: [] };

export default async function AnalyticsPage() {
  const report = await safeApiFetch<CostReport>("/analytics/costs", emptyReport);
  return <div className="space-y-7"><div><p className="eyebrow">COST & THROUGHPUT</p><h1 className="page-title">成本运营</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">按 Provider 回传或配置估算值统计，按币种隔离展示。用于生产运营观察，不替代服务商账单与财务结算。</p></div>
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{report.summaries.length ? report.summaries.map((summary) => <div className="metric-card" key={summary.currency}><p>{summary.currency} 回传/估算成本</p><strong>{(summary.reported_cost_minor / 100).toFixed(2)}</strong><p className="mt-3 text-xs">{summary.task_count} 个任务 · 成功率 {(summary.success_rate * 100).toFixed(1)}%</p></div>) : <div className="metric-card"><p>暂无可统计成本</p><strong>0</strong></div>}</section>
    <div className="grid items-start gap-6 xl:grid-cols-[.8fr_1.2fr]"><section className="panel h-fit min-w-0 overflow-hidden p-6"><h2 className="section-title mb-4">每日趋势</h2>{report.daily.length ? <div className="overflow-x-auto"><table className="data-table min-w-[480px]"><thead><tr><th>日期</th><th>币种</th><th>任务</th><th>成本</th></tr></thead><tbody>{report.daily.map((point) => <tr key={`${point.date}-${point.currency}`}><td>{point.date}</td><td>{point.currency}</td><td>{point.task_count}</td><td>{(point.reported_cost_minor / 100).toFixed(2)}</td></tr>)}</tbody></table></div> : <p className="empty-copy">任务完成后显示趋势。</p>}</section>
      <section className="panel min-w-0 overflow-hidden p-6"><h2 className="section-title mb-4">Provider / 平台 / SKU 明细</h2>{report.breakdown.length ? <div className="overflow-x-auto"><table className="data-table min-w-[720px]"><thead><tr><th>Provider</th><th>模型</th><th>平台</th><th>SKU</th><th>任务</th><th>成本</th></tr></thead><tbody>{report.breakdown.map((row) => <tr key={`${row.provider}-${row.model}-${row.platform}-${row.sku}-${row.currency}`}><td>{row.provider}</td><td>{row.model}</td><td>{row.platform}</td><td>{row.sku}</td><td>{row.task_count}</td><td>{row.currency} {(row.reported_cost_minor / 100).toFixed(2)}</td></tr>)}</tbody></table></div> : <p className="empty-copy">暂无生产明细。</p>}</section></div>
  </div>;
}
