"use client";

import { FormEvent, useState } from "react";

import { AdminUser, UserRole } from "@/lib/types";

const roleLabels: Record<UserRole, string> = { admin: "管理员", operator: "运营", designer: "设计", reviewer: "审核" };
const allRoles = Object.keys(roleLabels) as UserRole[];

export function UserAdmin({ initialUsers }: { initialUsers: AdminUser[] }) {
  const [users, setUsers] = useState(initialUsers);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    const form = event.currentTarget;
    const data = new FormData(form);
    const roles = allRoles.filter((role) => data.getAll("roles").includes(role));
    const response = await fetch("/api/backend/admin/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: data.get("email"), password: data.get("password"), roles }),
    });
    if (response.ok) {
      const created = await response.json();
      setUsers((current) => [...current, created]);
      form.reset();
      setMessage("用户已创建，操作已写入审计记录。");
    } else {
      const body = await response.json().catch(() => ({ detail: "创建失败" }));
      setMessage(body.detail ?? "创建失败");
    }
    setBusy(false);
  }

  async function save(user: AdminUser, roles: UserRole[], isActive: boolean) {
    setBusy(true);
    setMessage("");
    const response = await fetch(`/api/backend/admin/users/${user.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ roles, is_active: isActive }),
    });
    if (response.ok) {
      const updated = await response.json();
      setUsers((current) => current.map((item) => item.id === updated.id ? updated : item));
      setMessage(`${updated.email} 已更新。`);
    } else {
      const body = await response.json().catch(() => ({ detail: "保存失败" }));
      setMessage(body.detail ?? "保存失败");
    }
    setBusy(false);
  }

  return <div className="grid items-start gap-6 xl:grid-cols-[380px_1fr]">
    <section className="panel h-fit p-6">
      <h2 className="section-title">新增用户</h2>
      <form className="form-grid mt-5" onSubmit={create}>
        <div><label className="field-label mb-2" htmlFor="admin-email">邮箱</label><input className="field" id="admin-email" name="email" type="email" autoComplete="email" required /></div>
        <div><label className="field-label mb-2" htmlFor="admin-password">初始密码</label><input className="field" id="admin-password" name="password" type="password" autoComplete="new-password" minLength={12} required /></div>
        <fieldset className="rounded-xl border border-white/10 p-4"><legend className="px-2 text-xs font-semibold text-slate-300">角色（至少一项）</legend><div className="mt-2 grid grid-cols-2 gap-2">{allRoles.map((role) => <label className="flex min-h-11 items-center gap-2 text-sm text-slate-300" key={role}><input type="checkbox" name="roles" value={role} defaultChecked={role === "operator"} />{roleLabels[role]}</label>)}</div></fieldset>
        <button className="primary-button" disabled={busy}>{busy ? "处理中…" : "创建用户"}</button>
      </form>
    </section>
    <section className="panel min-w-0 p-6">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3"><div><h2 className="section-title">用户与角色</h2><p className="mt-2 text-sm text-slate-400">停用后现有令牌会立即失效；系统始终保留至少一个有效管理员。</p></div><span className="version-chip">{users.length} 个账户</span></div>
      <div className="space-y-3">{users.map((user) => <UserRow key={user.id} user={user} busy={busy} onSave={save} />)}</div>
      <p className="mt-5 min-h-5 text-sm text-orange-200" role="status" aria-live="polite">{message}</p>
    </section>
  </div>;
}

function UserRow({ user, busy, onSave }: { user: AdminUser; busy: boolean; onSave: (user: AdminUser, roles: UserRole[], isActive: boolean) => Promise<void> }) {
  const [roles, setRoles] = useState<UserRole[]>(user.roles);
  const [isActive, setIsActive] = useState(user.is_active);
  function toggle(role: UserRole) { setRoles((current) => current.includes(role) ? current.filter((item) => item !== role) : [...current, role]); }
  return <article className="rounded-2xl border border-white/8 p-4">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-semibold">{user.email}</p><p className="mt-1 text-xs text-slate-500">创建于 {new Date(user.created_at).toLocaleString("zh-CN")}</p></div><span className={isActive ? "status-pill" : "failure-pill"}>{isActive ? "有效" : "停用"}</span></div>
    <div className="mt-4 flex flex-wrap items-center gap-4">{allRoles.map((role) => <label className="flex min-h-11 items-center gap-2 text-sm text-slate-300" key={role}><input type="checkbox" checked={roles.includes(role)} onChange={() => toggle(role)} />{roleLabels[role]}</label>)}<label className="ml-auto flex min-h-11 items-center gap-2 text-sm text-slate-300"><input type="checkbox" checked={isActive} onChange={(event) => setIsActive(event.target.checked)} />允许登录</label><button className="secondary-button min-h-11" disabled={busy || !roles.length} onClick={() => onSave(user, roles, isActive)}>保存</button></div>
  </article>;
}
