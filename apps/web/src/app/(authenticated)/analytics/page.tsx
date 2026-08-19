import Link from "next/link";

import { AnalyticsFilters } from "@/features/analytics/analytics-filters";
import { safeApiFetch } from "@/lib/api-client";
import { CostReport, OperationsReport } from "@/lib/types";

const emptyCosts: CostReport = { generated_at: "", cost_basis: "provider_reported_or_estimated", summaries: [], daily: [], breakdown: [] };
const emptyOperations: OperationsReport = { generated_at: "", queued_count: 0, running_count: 0, review_pending_count: 0, failed_count: 0, total_calls: 0, succeeded_calls: 0, retry_calls: 0, success_rate: 0, retry_rate: 0, latency_p50_ms: 0, latency_p95_ms: 0, failure_classes: [], cost_groups: [], alerts: [] };

export default async function AnalyticsPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const incoming = await searchParams;
  const values = Object.fromEntries(["date_from", "date_to", "provider", "platform_slug", "sku", "status"].map((key) => [key, typeof incoming[key] === "string" ? incoming[key] : ""]));
  const costQuery = new URLSearchParams(Object.entries(values).filter(([key, value]) => value && key !== "status"));
  const operationsQuery = new URLSearchParams(Object.entries(values).filter(([, value]) => value));
  const [report, operations] = await Promise.all([
    safeApiFetch<CostReport>(`/analytics/costs?${costQuery}`, emptyCosts),
    safeApiFetch<OperationsReport>(`/analytics/operations?${operationsQuery}`, emptyOperations),
  ]);
  return <div className="space-y-7"><div><p className="eyebrow">COST & THROUGHPUT</p><h1 className="page-title">成本运营</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">成本为 Provider 回传或配置估算值，不替代服务商账单；延迟、失败和重试来自中台实际任务记录。未选择日期时默认统计最近 30 天。</p></div><AnalyticsFilters values={values} />
    {operations.alerts.length > 0 && <section className="space-y-3" aria-label="运营告警">{operations.alerts.map((alert) => <Link href={alert.action_url} className="failure-note block" key={alert.code}><strong>{alert.title}</strong><span className="ml-2">{alert.detail}</span></Link>)}</section>}
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><div className="metric-card"><p>模型调用</p><strong>{operations.total_calls}</strong><p className="mt-3 text-xs">成功率 {(operations.success_rate * 100).toFixed(1)}%</p></div><div className="metric-card"><p>排队 / 执行</p><strong>{operations.queued_count} / {operations.running_count}</strong></div><div className="metric-card"><p>P50 / P95 延迟</p><strong>{Math.round(operations.latency_p50_ms)} / {Math.round(operations.latency_p95_ms)}</strong><p className="mt-3 text-xs">毫秒</p></div><div className="metric-card"><p>失败 / 重试率</p><strong>{operations.failed_count} / {(operations.retry_rate * 100).toFixed(1)}%</strong></div></section>
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{report.summaries.length ? report.summaries.map((summary) => <div className="metric-card" key={summary.currency}><p>{summary.currency} 回传/估算成本</p><strong>{(summary.reported_cost_minor / 100).toFixed(2)}</strong><p className="mt-3 text-xs">{summary.task_count} 个任务 · 成功率 {(summary.success_rate * 100).toFixed(1)}%</p></div>) : <div className="metric-card"><p>暂无可统计成本</p><strong>0</strong></div>}</section>
    <div className="grid items-start gap-6 xl:grid-cols-[.7fr_1.3fr]"><section className="panel min-w-0 overflow-hidden p-6"><h2 className="section-title mb-4">失败分类</h2>{operations.failure_classes.length ? <div className="overflow-x-auto"><table className="data-table min-w-[360px]"><thead><tr><th>分类</th><th>数量</th><th>动作</th></tr></thead><tbody>{operations.failure_classes.map((row) => <tr key={row.classification}><td>{row.classification}</td><td>{row.count}</td><td><Link className="text-orange-300" href="/batches?status=failed">检查并重试</Link></td></tr>)}</tbody></table></div> : <p className="empty-copy">筛选范围内无失败。</p>}</section><section className="panel min-w-0 overflow-hidden p-6"><h2 className="section-title mb-4">Provider / 平台 / SKU 明细</h2>{report.breakdown.length ? <div className="overflow-x-auto"><table className="data-table min-w-[720px]"><thead><tr><th>Provider</th><th>模型</th><th>平台</th><th>SKU</th><th>任务</th><th>成本</th></tr></thead><tbody>{report.breakdown.map((row) => <tr key={`${row.provider}-${row.model}-${row.platform}-${row.sku}-${row.currency}`}><td>{row.provider}</td><td>{row.model}</td><td>{row.platform}</td><td>{row.sku}</td><td>{row.task_count}</td><td>{row.currency} {(row.reported_cost_minor / 100).toFixed(2)}</td></tr>)}</tbody></table></div> : <p className="empty-copy">暂无生产明细。</p>}</section></div>
  </div>;
}
