import { ProfileForm } from "@/features/talent/profile-form";

export default function NewTalentPage() {
  return <div className="mx-auto max-w-3xl space-y-7"><div><p className="eyebrow">NEW TALENT</p><h1 className="page-title">建立模特授权档案</h1><p className="mt-3 text-sm leading-6 text-slate-400">系统虚拟模特无需授权到期日；品牌真人模特必须记录有效期，过期后任务自动阻断。</p></div><section className="panel p-6 md:p-8"><ProfileForm /></section></div>;
}
