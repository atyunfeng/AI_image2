import { expect, test } from "@playwright/test";

test("operator imports a marketplace CSV and sees cost operations", async ({
  page,
}) => {
  const suffix = Date.now();
  const sku = `M5-E2E-${suffix}`;
  const modelName = `M5 批量 Mock ${suffix}`;
  const png = Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2nF8AAAAASUVORK5CYII=",
    "base64",
  );

  await page.goto("/login");
  await page.getByLabel("邮箱").fill("admin@aiimage.local");
  await page.getByLabel("密码").fill("LocalOnly-ChangeMe-2026");
  await page.getByRole("button", { name: "登录" }).click();
  await expect(
    page.getByRole("heading", { name: "电商视觉生产线" }),
  ).toBeVisible({ timeout: 15_000 });

  await page.goto("/models");
  await page.getByLabel("配置名称").fill(modelName);
  await page.getByLabel("模型 ID / 工作流名").fill("mock-m5-v1");
  await page.getByLabel("成本币种").fill("CNY");
  await page.getByRole("button", { name: "保存模型" }).click();
  await expect(
    page.getByText("模型配置已保存，密钥不会再次显示"),
  ).toBeVisible();

  await page.goto("/products/new");
  await page.getByLabel("SKU").fill(sku);
  await page.getByLabel("商品名称").fill("M5 批量平台测试衬衫");
  await page.getByRole("button", { name: "创建商品" }).click();
  await page
    .locator('input[type="file"]')
    .setInputFiles({ name: "front.png", mimeType: "image/png", buffer: png });
  await page.getByRole("button", { name: "上传参考图" }).click();
  await expect(page.getByText("参考图已固化")).toBeVisible();

  await page.goto("/bulk");
  await page
    .getByLabel("生图模型")
    .selectOption({ label: `${modelName} · mock-m5-v1` });
  const csv = Buffer.from(
    `sku,name,category,platform_slug,mode\n${sku},M5 批量平台测试衬衫,apparel,jd-cn,strict\n`,
  );
  await page
    .getByLabel("CSV 或 XLSX 文件")
    .setInputFiles({
      name: "m5-products.csv",
      mimeType: "text/csv",
      buffer: csv,
    });
  await page.getByRole("button", { name: "上传并创建任务" }).click();
  await expect(
    page.getByText("批量任务已进入后台队列，失败行不会影响成功行。"),
  ).toBeVisible();
  const importedRow = page.getByRole("row").filter({ hasText: sku });
  await expect(importedRow).toBeVisible();
  await expect(importedRow.getByRole("cell", { name: "jd-cn" })).toBeVisible();
  await expect(
    importedRow.getByRole("link", { name: "查看套图" }),
  ).toBeVisible({ timeout: 15_000 });

  await page.goto("/analytics");
  await expect(page.getByRole("heading", { name: "成本运营" })).toBeVisible();
  await expect(page.getByText(sku)).toBeVisible();
  await expect(page.getByText("Provider / 平台 / SKU 明细")).toBeVisible();
});
