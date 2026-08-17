import { expect, test } from "@playwright/test";

test("operator branches, masks, edits, composes, reviews, and exports one image", async ({ page }) => {
  const suffix = Date.now();
  const png = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2nF8AAAAASUVORK5CYII=", "base64");
  await page.goto("/login");
  await page.getByLabel("邮箱").fill("admin@aiimage.local");
  await page.getByLabel("密码").fill("LocalOnly-ChangeMe-2026");
  await page.getByRole("button", { name: "登录" }).click();
  await expect(page.getByRole("heading", { name: "电商视觉生产线" })).toBeVisible();

  await page.goto("/models");
  await page.getByLabel("配置名称").fill(`M4 编辑 Mock ${suffix}`);
  await page.getByLabel("模型 ID").fill("mock-edit-v1");
  await page.getByRole("checkbox", { name: "局部重绘 / 消除" }).check();
  await page.getByRole("checkbox", { name: "扩图" }).check();
  await page.getByRole("checkbox", { name: "自动抠背景" }).check();
  await page.getByRole("button", { name: "保存模型" }).click();
  await expect(page.getByText("模型配置已保存，密钥不会再次显示")).toBeVisible();

  await page.goto("/products/new");
  await page.getByLabel("SKU").fill(`M4-E2E-${suffix}`);
  await page.getByLabel("商品名称").fill("M4 单图微调测试商品");
  await page.getByRole("button", { name: "创建商品" }).click();
  await page.locator('input[type="file"]').setInputFiles({ name: "front.png", mimeType: "image/png", buffer: png });
  await page.getByRole("button", { name: "上传参考图" }).click();
  await expect(page.getByText("参考图已固化")).toBeVisible();

  await page.goto("/batches/new");
  const productValue = await page.getByLabel("商品").locator("option").filter({ hasText: `M4-E2E-${suffix}` }).getAttribute("value");
  const modelValue = await page.getByLabel("生图模型").locator("option").filter({ hasText: `M4 编辑 Mock ${suffix}` }).getAttribute("value");
  await page.getByLabel("商品").selectOption(productValue!);
  await page.getByLabel("生图模型").selectOption(modelValue!);
  await page.getByRole("button", { name: "启动生成" }).click();
  await expect(page.getByRole("button", { name: "微调此图" })).toBeEnabled({ timeout: 45_000 });
  await page.getByRole("button", { name: "微调此图" }).click();
  await expect(page).toHaveURL(/\/editing\/[0-9a-f-]+$/);

  const canvas = page.getByLabel("编辑蒙版画布");
  await canvas.scrollIntoViewIfNeeded();
  const bounds = await canvas.boundingBox();
  expect(bounds).not.toBeNull();
  await page.mouse.move(bounds!.x + bounds!.width * 0.35, bounds!.y + bounds!.height * 0.4);
  await page.mouse.down();
  await page.mouse.move(bounds!.x + bounds!.width * 0.65, bounds!.y + bounds!.height * 0.6, { steps: 8 });
  await page.mouse.up();
  await expect(page.getByText("已绘制蒙版")).toBeVisible();
  await page.getByLabel("修改要求").fill("只替换选区背景为柔和米色，商品主体保持不变");
  await page.getByRole("button", { name: "生成编辑版本" }).click();
  await expect(page.getByText("编辑任务已创建，正在生成和质检。")).toBeVisible();
  const revisionOne = page.getByRole("button", { name: /v1 · 局部替换/ });
  await expect(revisionOne).toBeEnabled({ timeout: 45_000 });
  await revisionOne.click();
  await expect(page.getByText("自动项通过", { exact: true })).toBeVisible();

  await page.getByLabel("权威文字图层").fill("秋季新品");
  await page.getByPlaceholder("版本备注（可选）").last().fill("新增权威标题");
  await page.getByRole("button", { name: "保存版式新版本" }).click();
  await expect(page.getByText("版式编辑已生成新版本并进入审核。")).toBeVisible();
  const revisionTwo = page.getByRole("button", { name: /v2 · 版式与图层/ });
  await expect(revisionTwo).toBeEnabled();
  await revisionTwo.click();
  await expect(page.getByText("自动项通过", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "进入人工审核" }).click();
  await page.getByRole("button", { name: "通过" }).click();
  await expect(page.getByRole("link", { name: "导出" })).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "导出" }).click();
  expect((await download).suggestedFilename()).toContain("batch-");
});
