import { safeApiFetch } from "@/lib/api-client";
import { AuditEventPage } from "@/lib/types";

export default async function AuditPage({ searchParams }: { searchParams: Promise<{ event_type?: string }> }) {
  const params = await searchParams;
  const query = params.event_type ? `?event_type=${encodeURIComponent(params.event_type)}` : "";
  const page = await safeApiFetch<AuditEventPage>(`/admin/audit${query}`, { total: 0, items: [] });
  return <div className="space-y-7"><div><h1 className="page-title">审计记录</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">敏感值在服务端脱敏；记录保留操作者、事件、对象和发生时间。</p></div><section className="panel min-w-0 p-6"><form className="mb-5 flex flex-wrap items-end gap-3"><div><label className="field-label mb-2" htmlFor="event-type">事件类型</label><input className="field" id="event-type" name="event_type" defaultValue={params.event_type} placeholder="例如 user.updated" /></div><button className="secondary-button min-h-11">筛选</button></form>{page.items.length ? <div className="overflow-x-auto"><table className="data-table min-w-[760px]"><thead><tr><th>时间</th><th>事件</th><th>操作者</th><th>详情</th></tr></thead><tbody>{page.items.map((event) => <tr key={event.id}><td>{new Date(event.created_at).toLocaleString("zh-CN")}</td><td>{event.event_type}</td><td className="font-mono text-xs">{event.actor_user_id?.slice(0, 8) ?? "system"}</td><td><pre className="max-w-xl whitespace-pre-wrap break-all text-xs text-slate-400">{JSON.stringify(event.details, null, 2)}</pre></td></tr>)}</tbody></table></div> : <p className="empty-copy">当前筛选条件下没有审计记录。</p>}<p className="mt-4 text-xs text-slate-500">共 {page.total} 条</p></section></div>;
}
