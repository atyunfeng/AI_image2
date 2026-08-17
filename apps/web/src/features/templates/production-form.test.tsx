import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { ProductionForm } from "./production-form";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }));

const products = [{ id: "product-1", sku: "SKU-1", name: "衬衫", category: "apparel" as const }];
const models = [{ id: "model-1", name: "Mock", provider: "mock", model_id: "mock-v1", base_url: null, billing_currency: "USD", provider_options: {}, capabilities: ["reference_to_image"], has_key: true, key_suffix: "test", is_enabled: true }];
const packs = [
  { id: "p1", version_id: "amazon-v1", slug: "amazon-global", name: "Amazon", kind: "platform" as const, version: 1, status: "published" as const, rules: {}, source: "first_party_default", published_at: "2026-08-17T00:00:00Z" },
  { id: "p2", version_id: "apparel-v1", slug: "apparel-core", name: "服装基础套图", kind: "category" as const, version: 1, status: "published" as const, rules: {}, source: "first_party_default", published_at: "2026-08-17T00:00:00Z" },
  { id: "p3", version_id: "brand-v1", slug: "brand-neutral", name: "中性品牌", kind: "brand" as const, version: 1, status: "published" as const, rules: {}, source: "first_party_default", published_at: "2026-08-17T00:00:00Z" },
];

it("previews platform-derived slots before execution", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      id: "plan-1",
      product_id: "product-1",
      mode: "strict",
      compiler_hash: "1234567890abcdef",
      created_at: "2026-08-17T00:00:00Z",
      compiled_snapshot: { packs: { platform: { slug: "amazon-global", version: 1 } } },
      items: [
        { id: "i1", position: 0, slot: "hero_front", label: "正面主图", requested_view: "front", width: 2000, height: 2000, prompt: "hero", rules: {} },
        { id: "i2", position: 1, slot: "detail_material", label: "材质详情", requested_view: "detail", width: 2000, height: 2000, prompt: "detail", authoritative_copy: "材质细节", rules: {} },
      ],
    }),
  }));
  render(<ProductionForm products={products} models={models} packs={packs} />);
  await userEvent.selectOptions(screen.getByLabelText("目标平台"), "amazon-v1");
  await userEvent.click(screen.getByRole("button", { name: "编译图片套装" }));
  expect(await screen.findByText("正面主图")).toBeVisible();
  expect(screen.getByText("2000 × 2000 · front")).toBeVisible();
  expect(screen.getByText("材质详情")).toBeVisible();
  expect(screen.getByRole("button", { name: "开始生成套图" })).toBeEnabled();
  vi.unstubAllGlobals();
});
