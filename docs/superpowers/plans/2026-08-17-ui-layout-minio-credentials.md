# UI Layout and MinIO Credentials Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复中台表单标题、面板和移动端表格错位，并让本地 MinIO 控制台凭据与后端对象存储配置保持一致且可查。

**Architecture:** 保留现有页面结构和视觉语言，只修正共享 CSS 与三个受影响页面的响应式约束。MinIO 使用同一组 Compose 环境变量同时配置服务端根账号和 API/worker 的 S3 客户端，README 明确区分中台账号与 MinIO 账号，不重置对象存储数据卷。

**Tech Stack:** Next.js 16、React 19、Tailwind CSS 4、Playwright 1.62、Docker Compose、MinIO

**Spec:** `docs/superpowers/specs/2026-08-17-ecommerce-ai-image-platform-design.md`

## Global Constraints

- 保留现有深色中台视觉语言，不重做信息架构。
- 不删除或重建 `minio-data` 数据卷。
- 本地默认凭据仅用于开发，生产部署必须覆盖。
- 页面在 1440×900、390×844 和 844×390 下不得出现视口级横向溢出。
- 表格内容较宽时在表格容器内横向滚动，不压缩到标题或单元格重叠。

---

### Task 1: Add layout regression coverage

**Files:**
- Create: `apps/web/e2e/layout-regression.spec.ts`

**Interfaces:**
- Consumes: 已有 `/login`、`/models`、`/bulk`、`/analytics` 页面与本地管理员账号
- Produces: Playwright 布局回归测试，检查标签与控件不重叠、页面不产生视口级横向溢出

- [x] **Step 1: Write the failing test**

```ts
import { expect, test } from "@playwright/test";

async function login(page: import("@playwright/test").Page) {
  await page.goto("/login");
  await page.getByLabel("邮箱").fill("admin@aiimage.local");
  await page.getByLabel("密码").fill("LocalOnly-ChangeMe-2026");
  await page.getByRole("button", { name: "登录" }).click();
}

test("forms and dense tables remain aligned on phone and desktop", async ({ page }) => {
  await login(page);
  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }, { width: 844, height: 390 }]) {
    await page.setViewportSize(viewport);
    for (const path of ["/models", "/bulk", "/analytics"]) {
      await page.goto(path);
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
      const overlaps = await page.locator("label[for]").evaluateAll((labels) => labels.filter((label) => {
        const control = document.getElementById(label.htmlFor);
        if (!control) return false;
        return label.getBoundingClientRect().bottom > control.getBoundingClientRect().top;
      }).map((label) => label.htmlFor));
      expect(overlaps).toEqual([]);
    }
  }
});
```

- [x] **Step 2: Run test to verify it fails**

Run: `pnpm --dir apps/web test:e2e layout-regression.spec.ts`

Expected: FAIL on the existing negative label margin or mobile viewport overflow.

- [x] **Step 3: Commit the regression test with the implementation in Task 2**

The test intentionally remains failing until the minimal layout fix is applied.

### Task 2: Correct shared spacing and responsive composition

**Files:**
- Modify: `apps/web/src/app/globals.css`
- Modify: `apps/web/src/app/(authenticated)/models/page.tsx`
- Modify: `apps/web/src/features/models/model-list.tsx`
- Modify: `apps/web/src/features/models/model-form.tsx`
- Modify: `apps/web/src/features/bulk/bulk-production.tsx`
- Modify: `apps/web/src/app/(authenticated)/analytics/page.tsx`

**Interfaces:**
- Consumes: `.field-label`, `.row-card`, `.data-table` and existing Tailwind layout classes
- Produces: consistent label gaps, content-height panels, phone-safe model rows and scrollable dense tables

- [x] **Step 1: Remove negative label spacing and add a phone row layout**

Change `.field-label` to use a normal line height without a negative bottom margin. Add a max-width 639px media rule that lets `.row-card` use two columns and places its metadata on a second row.

- [x] **Step 2: Prevent short panels from stretching to long sibling content**

Add `items-start` to the models, bulk and analytics two-column grids and `h-fit` to their short panels.

- [x] **Step 3: Make narrow paired controls and dense tables responsive**

Change fixed paired form grids to one column below `sm`. Add explicit `min-w-[640px]` or `min-w-[720px]` only to tables already inside `overflow-x-auto` containers.

- [x] **Step 4: Run the targeted UI tests**

Run: `pnpm --dir apps/web test && pnpm --dir apps/web test:e2e layout-regression.spec.ts`

Expected: PASS with no label/control overlap and no viewport-level horizontal overflow.

### Task 3: Unify and document MinIO credentials

**Files:**
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Modify: `README.md`

**Interfaces:**
- Consumes: `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` Compose substitutions
- Produces: identical MinIO server and backend S3 credentials with local defaults

- [x] **Step 1: Add the local MinIO variables**

Add these values to `.env.example`:

```dotenv
MINIO_ROOT_USER=aiimage
MINIO_ROOT_PASSWORD=local-development-secret
```

- [x] **Step 2: Use the same variables on both sides of MinIO authentication**

Use `${MINIO_ROOT_USER:-aiimage}` and `${MINIO_ROOT_PASSWORD:-local-development-secret}` for the MinIO service and the backend `AIIMAGE_S3_ACCESS_KEY` / `AIIMAGE_S3_SECRET_KEY` values.

- [x] **Step 3: Separate the two login surfaces in README**

Document the middle-platform administrator separately from the MinIO console root account and retain the local-only warning.

- [x] **Step 4: Validate Compose and live authentication without deleting data**

Run:

```bash
docker compose config --quiet
docker compose up -d --force-recreate minio api worker --wait
docker compose exec -T minio sh -c 'MC_HOST_verify=http://aiimage:local-development-secret@127.0.0.1:9000 mc ls verify >/dev/null'
```

Expected: Compose is valid, services are healthy, and S3 authentication succeeds with the documented defaults.

### Task 4: Final visual and build verification

**Files:**
- Test: `apps/web/e2e/layout-regression.spec.ts`

**Interfaces:**
- Consumes: repaired UI and synchronized local MinIO configuration
- Produces: desktop/mobile screenshots, successful production build, detector output and browser login evidence

- [x] **Step 1: Run the frontend quality gates**

Run: `pnpm --dir apps/web lint && pnpm --dir apps/web test && pnpm --dir apps/web build`

Expected: all commands exit 0.

- [x] **Step 2: Run the UI detector**

Run:

```bash
node /Users/chu/.codex/skills/impeccable/scripts/detect.mjs --json apps/web/src/app/globals.css apps/web/src/app/'(authenticated)'/models/page.tsx apps/web/src/features/models/model-list.tsx apps/web/src/features/models/model-form.tsx apps/web/src/features/bulk/bulk-production.tsx apps/web/src/app/'(authenticated)'/analytics/page.tsx
```

Expected: no newly introduced high-confidence UI violations.

- [x] **Step 3: Verify MinIO console login in a real browser engine**

Use Playwright with Microsoft Edge to log in to `http://localhost:9001` with the documented local root account and assert the URL ends in `/browser`.

- [ ] **Step 4: Commit, merge and verify main**

Commit the feature branch, merge it into `main`, rerun the targeted layout test and Compose validation from `main`, then push only when a configured remote is available.
