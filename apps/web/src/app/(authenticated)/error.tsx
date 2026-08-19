"use client";

import { useEffect } from "react";

export default function AuthenticatedError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <section className="panel mx-auto max-w-2xl p-7" role="alert">
      <h1 className="section-title">数据暂时无法加载</h1>
      <p className="mt-3 text-sm leading-6 text-slate-400">
        服务可能不可用，或者当前账户没有访问权限。请重试；如果问题持续，请联系管理员检查系统状态和角色配置。
      </p>
      <button className="primary-button mt-5" type="button" onClick={reset}>
        重新加载
      </button>
    </section>
  );
}
