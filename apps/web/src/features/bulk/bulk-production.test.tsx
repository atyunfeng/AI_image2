import { render, screen } from "@testing-library/react";

import { BulkProduction } from "./bulk-production";

const model = { id: "model-1", name: "批量 Mock", provider: "mock", model_id: "mock-v1", base_url: null, billing_currency: "CNY", provider_options: {}, capabilities: ["reference_to_image"], has_key: false, key_suffix: null, is_enabled: true };
const pack = (id: string, name: string, kind: "category" | "brand") => ({ id, version_id: `${id}-v1`, slug: id, name, kind, version: 1, status: "published" as const, rules: {}, source: "first_party_default", published_at: "2026-08-17T00:00:00Z" });

it("offers CSV preflight and execution inputs", () => {
  render(<BulkProduction models={[model]} packs={[pack("apparel", "服装", "category"), pack("neutral", "中性", "brand")]} initialJobs={[]} />);
  expect(screen.getByLabelText("CSV 文件")).toBeVisible();
  expect(screen.getByLabelText("生图模型")).toHaveValue("model-1");
  expect(screen.getByText("仅预检 CSV")).toBeVisible();
  expect(screen.getByRole("button", { name: "上传并创建任务" })).toBeEnabled();
});
