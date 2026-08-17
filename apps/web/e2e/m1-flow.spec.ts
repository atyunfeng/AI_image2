import { expect, test } from "@playwright/test";

test("operator creates, generates, approves, and exports one SKU", async ({ page }) => {
  const suffix = Date.now();
  await page.goto("/login");
  await page.getByLabel("邮箱").fill("admin@aiimage.local");
  await page.getByLabel("密码").fill("LocalOnly-ChangeMe-2026");
  await page.getByRole("button", { name: "登录" }).click();
  await expect(page.getByText("电商视觉生产线")).toBeVisible();

  await page.goto("/models");
  await page.getByPlaceholder("配置名称").fill(`E2E Mock ${suffix}`);
  await page.getByPlaceholder("模型 ID").fill("mock-v1");
  await page.getByRole("button", { name: "保存模型" }).click();
  await expect(page.getByText("模型配置已保存，密钥不会再次显示")).toBeVisible();

  await page.goto("/products/new");
  await page.getByLabel("SKU").fill(`E2E-${suffix}`);
  await page.getByLabel("商品名称").fill("E2E 测试连衣裙");
  await page.getByRole("button", { name: "创建商品" }).click();
  await expect(page.getByText("E2E 测试连衣裙")).toBeVisible();
  const png = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2nF8AAAAASUVORK5CYII=", "base64");
  await page.locator('input[type="file"]').setInputFiles({ name: "front.png", mimeType: "image/png", buffer: png });
  await page.getByRole("button", { name: "上传参考图" }).click();
  await expect(page.getByText("参考图已固化")).toBeVisible();

  await page.goto("/batches/new");
  await page.getByRole("button", { name: "启动生成" }).click();
  await expect(page.getByRole("button", { name: "通过" })).toBeEnabled({ timeout: 45_000 });
  await page.getByRole("button", { name: "通过" }).click();
  await expect(page.getByRole("link", { name: "导出" })).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "导出" }).click();
  expect((await download).suggestedFilename()).toContain("batch-");
});
