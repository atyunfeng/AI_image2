import { expect, test } from "@playwright/test";

test("operator compiles, generates, quality-checks, and exports a platform image", async ({ page }) => {
  const suffix = Date.now();
  await page.goto("/login");
  await page.getByLabel("邮箱").fill("admin@aiimage.local");
  await page.getByLabel("密码").fill("LocalOnly-ChangeMe-2026");
  await page.getByRole("button", { name: "登录" }).click();
  await expect(page.getByRole("heading", { name: "电商视觉生产线" })).toBeVisible();

  await page.goto("/models");
  await page.getByPlaceholder("配置名称").fill(`M2 E2E Mock ${suffix}`);
  await page.getByPlaceholder("模型 ID").fill("mock-v1");
  await page.getByRole("button", { name: "保存模型" }).click();
  await expect(page.getByText("模型配置已保存，密钥不会再次显示")).toBeVisible();

  await page.goto("/products/new");
  await page.getByLabel("SKU").fill(`M2-E2E-${suffix}`);
  await page.getByLabel("商品名称").fill("M2 平台套图测试衬衫");
  await page.getByRole("button", { name: "创建商品" }).click();
  await expect(page.getByRole("heading", { name: "M2 平台套图测试衬衫" })).toBeVisible();
  const png = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2nF8AAAAASUVORK5CYII=", "base64");
  await page.locator('input[type="file"]').setInputFiles({ name: "front.png", mimeType: "image/png", buffer: png });
  await page.getByRole("button", { name: "上传参考图" }).click();
  await expect(page.getByText("参考图已固化")).toBeVisible();

  await page.goto("/production/new");
  await page.getByLabel("目标平台").selectOption({ label: "Amazon（全球默认） · v1" });
  await page.getByRole("button", { name: "编译图片套装" }).click();
  await expect(page.getByRole("heading", { name: "已编译 3 张图片" })).toBeVisible();
  await expect(page.getByText("正面主图")).toBeVisible();
  await expect(page.getByText("材质详情")).toBeVisible();
  await page.getByRole("button", { name: "开始生成套图" }).click();
  await expect(page).toHaveURL(/\/production\//);

  await expect(page.getByText("结构质检")).toHaveCount(3, { timeout: 60_000 });
  await expect(page.getByText("通过", { exact: true })).toHaveCount(3);
  await page.getByRole("link", { name: "查看与审核" }).first().click();
  await expect(page.getByRole("button", { name: "通过" })).toBeEnabled();
  await page.getByRole("button", { name: "通过" }).click();
  await expect(page.getByRole("link", { name: "导出" })).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "导出" }).click();
  expect((await download).suggestedFilename()).toContain("batch-");
});
