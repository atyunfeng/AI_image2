import { apiReadiness } from "@/lib/api-client";

const labels: Record<string, string> = {
  database: "数据库",
  redis: "队列",
  object_store: "对象存储",
  worker: "生成 Worker",
};

export async function ServiceState() {
  const readiness = await apiReadiness();
  const failed = Object.entries(readiness.checks)
    .filter(([, healthy]) => !healthy)
    .map(([name]) => labels[name] ?? name);
  const ready = readiness.status === "ready";
  return (
    <span
      className={ready ? "status-pill" : "failure-pill"}
      title={ready ? "数据库、队列、对象存储和 Worker 均可用" : `不可用：${failed.join("、") || "API"}`}
      role="status"
    >
      {ready ? "系统就绪" : "系统降级"}
    </span>
  );
}
