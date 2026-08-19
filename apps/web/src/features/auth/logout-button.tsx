import { logoutAction } from "@/lib/session";

export function LogoutButton() {
  return (
    <form action={logoutAction}>
      <button className="account-action" type="submit">退出登录</button>
    </form>
  );
}
