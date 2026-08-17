import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { LoginForm } from "./login-form";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }));
vi.mock("@/lib/session", () => ({ loginAction: vi.fn() }));

it("submits email and password", async () => {
  const login = vi.fn().mockResolvedValue({ ok: true }); render(<LoginForm login={login} />);
  await userEvent.type(screen.getByLabelText("邮箱"), "admin@aiimage.local"); await userEvent.type(screen.getByLabelText("密码"), "LocalOnly-ChangeMe-2026"); await userEvent.click(screen.getByRole("button", { name: "登录" }));
  expect(login).toHaveBeenCalledWith({ email: "admin@aiimage.local", password: "LocalOnly-ChangeMe-2026" });
});
