import { expect, test, type Page } from "@playwright/test";

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("邮箱").fill("admin@aiimage.local");
  await page.getByLabel("密码").fill("LocalOnly-ChangeMe-2026");
  await page.getByRole("button", { name: "登录" }).click();
  await expect(
    page.getByRole("heading", { name: "电商视觉生产线" }),
  ).toBeVisible({ timeout: 15_000 });
}

test("forms and dense tables remain aligned on phone and desktop", async ({
  page,
}) => {
  await login(page);

  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 375, height: 812 },
    { width: 390, height: 844 },
    { width: 844, height: 390 },
  ]) {
    await page.setViewportSize(viewport);

    for (const path of ["/models", "/bulk", "/analytics"]) {
      await page.goto(path);
      await expect
        .poll(() =>
          page.evaluate(
            () => document.documentElement.scrollWidth <= window.innerWidth,
          ),
        )
        .toBe(true);

      const overlappingLabels = await page
        .locator("label[for]")
        .evaluateAll((labels) =>
          labels
            .filter((label) => {
              const htmlFor = label.getAttribute("for");
              if (!htmlFor) return false;
              const control = document.getElementById(htmlFor);
              if (!control) return false;
              return (
                label.getBoundingClientRect().bottom >
                control.getBoundingClientRect().top
              );
            })
            .map((label) => label.getAttribute("for")),
        );

      expect(overlappingLabels).toEqual([]);
    }
  }
});
