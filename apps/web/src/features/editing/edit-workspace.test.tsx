import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { EditWorkspace } from "./edit-workspace";

vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn(), push: vi.fn() }) }));

const project = { id: "project-1", name: "主图微调", product_id: "product-1", source_batch_id: "batch-1", source_asset_id: "asset-1", created_at: "2026-08-17T00:00:00Z", revisions: [{ id: "revision-0", project_id: "project-1", parent_revision_id: null, version: 0, snapshot_label: "原始生成图", operation: "source", capability: null, status: "ready", source_asset_id: "asset-1", mask_asset_id: null, output_asset_id: "asset-1", prompt: null, parameters: {}, batch_id: null, created_at: "2026-08-17T00:00:00Z" }] };
const models = [
  { id: "inpaint", name: "局部重绘模型", provider: "mock", model_id: "edit", base_url: null, capabilities: ["inpaint"], has_key: false, key_suffix: null, is_enabled: true },
  { id: "outpaint", name: "扩图模型", provider: "mock", model_id: "expand", base_url: null, capabilities: ["outpaint"], has_key: false, key_suffix: null, is_enabled: true },
];

it("switches the eligible model when the edit capability changes", async () => {
  render(<EditWorkspace project={project} models={models} evidence={{}} />);
  expect(screen.getByRole("option", { name: /局部重绘模型/ })).toBeVisible();
  await userEvent.selectOptions(screen.getByLabelText("编辑动作"), "outpaint");
  expect(screen.getByRole("option", { name: /扩图模型/ })).toBeVisible();
  expect(screen.getByRole("button", { name: "画笔" })).toBeVisible();
  expect(screen.getByRole("button", { name: "撤销" })).toBeDisabled();
});
