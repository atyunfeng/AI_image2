import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { FashionForm } from "./fashion-form";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }));

const products = [{ id: "product-1", sku: "SKU-1", name: "测试外套", category: "apparel" as const, references: [] }];
const profiles = [{ id: "profile-1", name: "虚拟模特 A", profile_type: "system_virtual" as const, authorization_status: "not_required" as const, authorization_expires_on: null, attributes: {}, is_active: true, is_selectable: true, created_at: "2026-08-17T00:00:00Z", references: [] }];
const models = [{ id: "model-1", name: "全能力模型", provider: "mock", model_id: "mock-fashion", base_url: null, capabilities: ["reference_to_image", "multi_reference_to_image", "virtual_try_on"], has_key: false, key_suffix: null, is_enabled: true }];

it("filters models by the capabilities required by selected outputs", async () => {
  render(<FashionForm products={products} profiles={profiles} models={models} />);
  expect(screen.getByRole("option", { name: /全能力模型/ })).toBeVisible();
  await userEvent.click(screen.getByText("模特侧面图"));
  expect(screen.getByRole("button", { name: /开始生成 4 张图片/ })).toBeEnabled();
});
