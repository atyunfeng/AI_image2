import { redirect } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { apiFetch } from "@/lib/api-client";

export default async function AuthenticatedLayout({ children }: LayoutProps<"/">) {
  let user: { email: string; roles: string[] };
  try { user = await apiFetch<{ email: string; roles: string[] }>("/auth/me"); } catch { redirect("/login"); }
  return <AppShell email={user.email} roles={user.roles}>{children}</AppShell>;
}
