import { expect, test, type Page } from "@playwright/test";

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("邮箱").fill("admin@aiimage.local");
  await page.getByLabel("密码").fill("LocalOnly-ChangeMe-2026");
  await page.getByRole("button", { name: "登录" }).click();
  try {
    await page.waitForURL((url) => url.pathname === "/", { timeout: 15_000 });
  } catch {
    await page.getByLabel("邮箱").fill("admin@aiimage.local");
    await page.getByLabel("密码").fill("LocalOnly-ChangeMe-2026");
    await page.getByRole("button", { name: "登录" }).click();
    await page.waitForURL((url) => url.pathname === "/", { timeout: 15_000 });
  }
  await expect(
    page.getByRole("heading", { name: "电商视觉生产线" }),
  ).toBeVisible();
}

test("M6 governance, truth, templates, per-image controls, layers, export, and operations", async ({
  page,
}) => {
  const suffix = Date.now();
  const sku = `M6-E2E-${suffix}`;
  const modelName = `M6 Mock ${suffix}`;
  const png = Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAIAAADZF8uwAAAAFElEQVR42mP8//8/AymAiSTVoxpRAgC6tQMVIcQ3WQAAAABJRU5ErkJggg==",
    "base64",
  );
  await login(page);

  await page.goto("/admin/users");
  await page.getByLabel("邮箱").fill(`operator-${suffix}@example.com`);
  await page.getByLabel("初始密码").fill("Operator-Password-2026");
  await page.getByRole("button", { name: "创建用户" }).click();
  await expect(
    page.getByText("用户已创建，操作已写入审计记录。"),
  ).toBeVisible();

  await page.goto("/models");
  await page.getByLabel("配置名称").fill(modelName);
  await page.getByLabel("模型 ID / 工作流名").fill("mock-m6-v1");
  await page.getByRole("button", { name: "保存模型" }).click();
  await expect(
    page.getByText("模型配置已保存，密钥不会再次显示"),
  ).toBeVisible();

  await page.goto("/products/new");
  await page.getByLabel("SKU").fill(sku);
  await page.getByLabel("商品名称").fill("M6 商品");
  await page.getByLabel("品牌").fill("Codex Studio");
  await page.getByRole("button", { name: "创建商品" }).click();
  await page
    .locator('input[type="file"]')
    .setInputFiles({ name: "front.png", mimeType: "image/png", buffer: png });
  await page.getByRole("button", { name: "上传参考图" }).click();
  await expect(page.getByText("参考图已固化")).toBeVisible();
  await page.getByLabel("商品名称").fill("M6 商品已更新");
  await page.getByRole("button", { name: "保存资料" }).click();
  await expect(page.getByText("商品资料已更新。")).toBeVisible();
  await page
    .getByLabel("人工确认 JSON")
    .fill('{"material":"cotton","primary_color":"white"}');
  await page.getByRole("button", { name: "保存新版本" }).click();
  await expect(page.getByText(/真值锚点 v2 已保存/)).toBeVisible();

  await page.goto("/templates");
  await page.getByLabel("唯一标识").fill(`brand-m6-${suffix}`);
  await page.getByLabel("名称").fill("M6 品牌规则");
  await page.getByLabel("类型", { exact: true }).selectOption("brand");
  await page
    .getByLabel("规则 JSON")
    .fill('{"prompt_suffix":"clean editorial"}');
  await page.getByRole("button", { name: "创建草稿" }).click();
  await expect(page.getByText("模板包草稿 v1 已创建。")).toBeVisible();
  const authoredPack = page
    .locator("article")
    .filter({ hasText: `brand-m6-${suffix}` });
  await authoredPack.getByRole("button", { name: "发布" }).click();
  await expect(page.getByText("v1 已发布，历史版本保持不可变。")).toBeVisible();

  await page.goto("/production/new");
  await page
    .getByLabel("商品 SKU")
    .selectOption({ label: `${sku} · M6 商品已更新` });
  await page.getByRole("button", { name: "编译图片套装" }).click();
  await expect(
    page.getByRole("heading", { name: /逐图核对与覆盖/ }),
  ).toBeVisible();
  const firstItem = page.locator("details.plan-slot").first();
  await firstItem.locator("summary").click();
  await firstItem.locator('input[name="label"]').fill("M6 自定义主图");
  await firstItem
    .locator('textarea[name="provider_parameters"]')
    .fill('{"seed":6}');
  await firstItem.getByRole("button", { name: "保存本图参数" }).click();
  await expect(page.getByText(/参数已保存/)).toBeVisible();
  await page
    .getByLabel("生图模型")
    .selectOption({ label: `${modelName} · mock-m6-v1` });
  await page.getByRole("button", { name: "开始生成套图" }).click();
  await expect(
    page.getByRole("heading", { name: "套图生成进度" }),
  ).toBeVisible();
  const firstBatch = page.getByRole("link", { name: "查看与审核" }).first();
  await expect(firstBatch).toBeVisible({ timeout: 45_000 });
  await firstBatch.click();
  await expect(page.getByRole("button", { name: "微调此图" })).toBeEnabled({
    timeout: 45_000,
  });
  await page.getByRole("button", { name: "微调此图" }).click();

  await page.getByRole("button", { name: "商品主体" }).click();
  await expect(page.getByText(/foreground 蒙版已生成/)).toBeVisible();
  const layerDetails = page.locator("details").filter({
    has: page.locator("summary").filter({ hasText: "新增图层" }),
  });
  await layerDetails.locator("summary").click();
  const layerForm = layerDetails.locator("form");
  await layerForm.locator('input[name="name"]').fill("M6 标题");
  await layerForm
    .locator('textarea[name="content"]')
    .fill(
      '{"text":"M6 新品","region":[40,40,900,180],"font_size":48,"color":"#16181d"}',
    );
  await layerForm.getByRole("button", { name: "新增图层" }).click();
  await expect(page.getByText("图层已创建。")).toBeVisible();
  await page.getByRole("button", { name: "合成为新版本" }).click();
  await expect(page.getByText("图层已合成为新的不可变版本。")).toBeVisible();

  const composedRevision = page.getByRole("button", {
    name: /v1 · 版式与图层/,
  });
  await expect(composedRevision).toBeEnabled();
  await composedRevision.click();
  await page.getByRole("link", { name: "进入人工审核" }).click();
  await page.getByRole("button", { name: "通过" }).click();
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "导出" }).click();
  expect((await download).suggestedFilename()).toContain("batch-");
  await page.reload();
  await expect(page.getByRole("heading", { name: "导出历史" })).toBeVisible();

  await page.goto("/admin/audit?event_type=batch.exported");
  await expect(
    page.getByText("batch.exported", { exact: true }).first(),
  ).toBeVisible();
  await page.goto(`/analytics?sku=${sku}`);
  await expect(page.getByRole("heading", { name: "成本运营" })).toBeVisible();
  await expect(page.getByText(sku).first()).toBeVisible();
});

test("new M6 administration pages stay within phone and desktop viewports", async ({
  page,
}) => {
  await login(page);
  for (const viewport of [
    { width: 375, height: 812 },
    { width: 1440, height: 900 },
  ]) {
    await page.setViewportSize(viewport);
    for (const path of [
      "/admin/users",
      "/admin/audit",
      "/templates",
      "/analytics",
    ]) {
      await page.goto(path);
      await expect
        .poll(() =>
          page.evaluate(
            () => document.documentElement.scrollWidth <= window.innerWidth,
          ),
        )
        .toBe(true);
    }
  }
});
