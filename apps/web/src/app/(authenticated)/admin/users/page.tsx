import { UserAdmin } from "@/features/admin/user-admin";
import { safeApiFetch } from "@/lib/api-client";
import { AdminUser } from "@/lib/types";

export default async function AdminUsersPage() {
  const users = await safeApiFetch<AdminUser[]>("/admin/users", []);
  return <div className="space-y-7"><div><h1 className="page-title">用户治理</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">由后端角色权限保护用户生命周期；密码只可设置和轮换，不会回显。</p></div><UserAdmin initialUsers={users} /></div>;
}
