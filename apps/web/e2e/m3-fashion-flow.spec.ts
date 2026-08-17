import { expect, test } from "@playwright/test";

const png = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2nF8AAAAASUVORK5CYII=",
  "base64",
);

async function uploadCurrentView(
  page: import("@playwright/test").Page,
  view: string,
  name: string,
  expectedCount: number,
) {
  await page.getByLabel("参考视角").selectOption(view);
  await page
    .locator('input[type="file"]')
    .setInputFiles({ name, mimeType: "image/png", buffer: png });
  await page.getByRole("button", { name: "上传参考图" }).click();
  await expect(page.locator('img[alt$="模特参考图"]')).toHaveCount(
    expectedCount,
  );
}

test("operator creates authorized talent, multi-angle images, virtual try-on, and exports", async ({
  page,
}) => {
  const suffix = Date.now();
  await page.goto("/login");
  await page.getByLabel("邮箱").fill("admin@aiimage.local");
  await page.getByLabel("密码").fill("LocalOnly-ChangeMe-2026");
  await page.getByRole("button", { name: "登录" }).click();
  await expect(
    page.getByRole("heading", { name: "电商视觉生产线" }),
  ).toBeVisible({ timeout: 15_000 });

  await page.goto("/models");
  await page.getByLabel("配置名称").fill(`M3 全能力 Mock ${suffix}`);
  await page.getByLabel("模型 ID").fill("mock-fashion-v1");
  await page.getByRole("checkbox", { name: "模特多角度" }).check();
  await page.getByRole("checkbox", { name: "虚拟试穿" }).check();
  await page.getByRole("button", { name: "保存模型" }).click();
  await expect(
    page.getByText("模型配置已保存，密钥不会再次显示"),
  ).toBeVisible();

  await page.goto("/talent/new");
  await page.getByLabel("模特名称").fill(`M3 虚拟模特 ${suffix}`);
  await page.getByRole("button", { name: "创建并上传参考图" }).click();
  await expect(page).toHaveURL(/\/talent\//);
  for (const [index, view] of ["front", "side", "back"].entries()) {
    await uploadCurrentView(page, view, `model-${view}.png`, index + 1);
    await expect(page.getByText("参考视角已固化")).toBeVisible();
  }
  await expect(page.getByText("可用于生图", { exact: true })).toBeVisible();

  await page.goto("/products/new");
  await page.getByLabel("SKU").fill(`M3-E2E-${suffix}`);
  await page.getByLabel("商品名称").fill("M3 多角度试穿外套");
  await page.getByLabel("品类").selectOption("apparel");
  await page.getByRole("button", { name: "创建商品" }).click();
  await expect(
    page.getByRole("heading", { name: "M3 多角度试穿外套" }),
  ).toBeVisible();
  const productUrl = page.url();
  for (const view of ["front"]) {
    await page.locator('select[name="view"]').selectOption(view);
    await page.locator('input[type="file"]').setInputFiles({
      name: `product-${view}.png`,
      mimeType: "image/png",
      buffer: png,
    });
    await page.getByRole("button", { name: "上传参考图" }).click();
    await expect(page.getByText("参考图已固化")).toBeVisible();
  }

  await page.goto("/fashion/new");
  let productOption = await page
    .getByLabel("服装 / 鞋 / 帽商品")
    .locator("option")
    .filter({ hasText: `M3-E2E-${suffix}` })
    .getAttribute("value");
  let profileOption = await page
    .getByLabel("授权模特")
    .locator("option")
    .filter({ hasText: `M3 虚拟模特 ${suffix}` })
    .getAttribute("value");
  let modelOption = await page
    .getByLabel("生图模型")
    .locator("option")
    .filter({ hasText: `M3 全能力 Mock ${suffix}` })
    .getAttribute("value");
  await page.getByLabel("服装 / 鞋 / 帽商品").selectOption(productOption!);
  await page.getByLabel("授权模特").selectOption(profileOption!);
  await page.getByLabel("生图模型").selectOption(modelOption!);
  await page.getByText("模特侧面图").click();
  await page.getByRole("button", { name: "开始生成 4 张图片" }).click();
  await expect(page.getByRole("status")).toContainText(
    "requires product reference: side",
  );

  await page.goto(productUrl);
  for (const view of ["side", "back"]) {
    await page.locator('select[name="view"]').selectOption(view);
    await page.locator('input[type="file"]').setInputFiles({
      name: `product-${view}.png`,
      mimeType: "image/png",
      buffer: png,
    });
    await page.getByRole("button", { name: "上传参考图" }).click();
    await expect(page.getByText("参考图已固化")).toBeVisible();
    await page.reload();
    await expect(page.locator('img[alt$="参考图"]')).toHaveCount(
      view === "side" ? 2 : 3,
    );
  }

  await page.goto("/fashion/new");
  productOption = await page
    .getByLabel("服装 / 鞋 / 帽商品")
    .locator("option")
    .filter({ hasText: `M3-E2E-${suffix}` })
    .getAttribute("value");
  profileOption = await page
    .getByLabel("授权模特")
    .locator("option")
    .filter({ hasText: `M3 虚拟模特 ${suffix}` })
    .getAttribute("value");
  modelOption = await page
    .getByLabel("生图模型")
    .locator("option")
    .filter({ hasText: `M3 全能力 Mock ${suffix}` })
    .getAttribute("value");
  await page.getByLabel("服装 / 鞋 / 帽商品").selectOption(productOption!);
  await page.getByLabel("授权模特").selectOption(profileOption!);
  await page.getByLabel("生图模型").selectOption(modelOption!);
  await page.getByText("模特侧面图").click();
  await page.getByText("模特背面图").click();
  await page.getByText("商品细节图").click();
  await page.getByRole("button", { name: "开始生成 6 张图片" }).click();
  await expect(page).toHaveURL(/\/fashion\/(?!new$)[0-9a-f-]+$/, {
    timeout: 15_000,
  });

  await expect(page.getByText("服饰质检")).toHaveCount(6, { timeout: 60_000 });
  await expect(page.getByText("自动项通过", { exact: true })).toHaveCount(6, {
    timeout: 60_000,
  });
  await page.getByRole("link", { name: "查看与人工审核" }).first().click();
  await page.getByRole("button", { name: "通过" }).click();
  await expect(page.getByRole("link", { name: "导出" })).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "导出" }).click();
  expect((await download).suggestedFilename()).toContain("batch-");
});
