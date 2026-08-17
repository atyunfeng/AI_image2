# M2 Platform Rules and Detail Images Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add versioned Taobao/Tmall, Amazon, and TikTok Shop rule packs, compile them with apparel and brand packs into multi-image production plans, render deterministic text layers, and block non-compliant outputs before review.

**Architecture:** Add a `templates` domain that owns immutable platform, category, and brand pack versions and compiles their intersection into an ordered generation plan. Keep generation execution in the existing durable workflow by creating one batch per compiled image slot and linking them with a production-plan identifier. Add a deterministic Pillow compositor and a structural QA service; generated base images remain immutable and composed derivatives record parentage.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy 2, Alembic, Pillow, PostgreSQL 17, Next.js 16, React 19, TypeScript 5.9, pytest, Vitest, Playwright, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-08-17-ecommerce-ai-image-platform-design.md`

## Global Constraints

- This plan covers M2 only: first-party platform packs, apparel/category packs, brand packs, deterministic text composition, plan compilation, and structural QA.
- Virtual models, virtual try-on, cross-view consistency, mask painting, inpainting, and outpainting remain M3-M4 work.
- Platform packs are versioned and immutable after publication; a generation plan stores the exact pack identifiers and versions it compiled.
- Authoritative price, specification, and promotion copy is rendered deterministically, never entrusted to the image model.
- Strict mode cannot compile an unsupported view when the product lacks a matching reference.
- Existing PostgreSQL authority, Redis delivery-hint, immutable asset, encrypted key, review, audit, and export guarantees remain unchanged.
- First-party rule values are product defaults and must be revalidated before a production platform policy release; do not claim official platform certification.
- Use targeted tests per task and run `bash scripts/verify-m2.sh` only for final integration.

## File and Responsibility Map

```text
backend/src/aiimage/templates/
├── models.py       # immutable versioned pack and compiled plan records
├── schemas.py      # API and compiler input/output contracts
├── presets.py      # first-party Taobao/Tmall, Amazon, TikTok Shop and apparel defaults
├── compiler.py     # deterministic pack intersection and strict-reference validation
├── service.py      # publish/list/compile transaction boundary
└── router.py       # template and production-plan HTTP API
backend/src/aiimage/composition/
├── text.py         # deterministic Pillow text layer rendering
└── service.py      # immutable derivative creation and provenance
backend/src/aiimage/quality/
├── rules.py        # structural file/platform checks
├── service.py      # persist check results and gate review
└── schemas.py      # quality evidence response
apps/web/src/features/templates/  # pack selector and compiled plan preview
apps/web/src/features/batches/    # multi-slot production-plan submission and status
```

---

### Task 1: Versioned Rule-Pack Domain and First-Party Presets

**Files:**
- Create: `backend/src/aiimage/templates/__init__.py`
- Create: `backend/src/aiimage/templates/models.py`
- Create: `backend/src/aiimage/templates/schemas.py`
- Create: `backend/src/aiimage/templates/presets.py`
- Create: `backend/src/aiimage/templates/service.py`
- Create: `backend/src/aiimage/templates/router.py`
- Create: `backend/alembic/versions/0006_template_packs.py`
- Modify: `backend/src/aiimage/api/main.py`
- Modify: `backend/alembic/env.py`
- Test: `backend/tests/templates/test_presets.py`
- Test: `backend/tests/templates/test_pack_api.py`

**Interfaces:**
- Consumes: authenticated SQLAlchemy sessions and audit service.
- Produces: `PackKind`, `TemplatePack`, `TemplatePackVersion`, `list_published_packs()`, and `GET /api/v1/template-packs`.

- [ ] **Step 1: Write failing preset and immutability tests**

```python
def test_first_party_presets_cover_initial_platforms() -> None:
    assert {pack.slug for pack in first_party_platform_packs()} == {
        "taobao-tmall-cn", "amazon-global", "tiktok-shop-global"
    }

async def test_published_pack_version_cannot_be_mutated(client, admin_headers) -> None:
    response = await client.patch(
        "/api/v1/template-packs/taobao-tmall-cn/versions/1",
        headers=admin_headers,
        json={"rules": {"background": "changed"}},
    )
    assert response.status_code == 409
```

- [ ] **Step 2: Run tests and verify they fail because the templates package does not exist**

Run: `uv run --project backend pytest backend/tests/templates/test_presets.py backend/tests/templates/test_pack_api.py -v`

- [ ] **Step 3: Implement immutable pack records and explicit preset data**

Define platform rules with `canvas`, `background`, `safe_margin`, `allowed_text_regions`, `max_file_bytes`, `format`, and ordered `slots`. Define one apparel category pack with `hero_front`, `detail_material`, and `detail_feature` slots. Publish presets idempotently at application startup; updates create a new version and never alter a published row.

- [ ] **Step 4: Expose read APIs and run the targeted tests**

Run: `uv run --project backend pytest backend/tests/templates -v`
Expected: all template preset and API tests pass.

- [ ] **Step 5: Commit the pack domain**

```bash
git add backend/src/aiimage/templates backend/alembic backend/tests/templates backend/src/aiimage/api/main.py
git commit -m "feat: add versioned commerce rule packs"
```

### Task 2: Deterministic Production-Plan Compiler

**Files:**
- Create: `backend/src/aiimage/templates/compiler.py`
- Create: `backend/tests/templates/test_compiler.py`
- Modify: `backend/src/aiimage/templates/models.py`
- Modify: `backend/src/aiimage/templates/schemas.py`
- Modify: `backend/src/aiimage/templates/service.py`
- Modify: `backend/src/aiimage/templates/router.py`
- Create: `backend/alembic/versions/0007_production_plans.py`

**Interfaces:**
- Consumes: `compile_plan(product, references, platform_version, category_version, brand_version, mode)`.
- Produces: immutable `ProductionPlan` and ordered `ProductionPlanItem` rows; `POST /api/v1/production-plans/compile`.

- [ ] **Step 1: Write failing compiler tests**

```python
def test_compile_intersects_platform_category_and_brand_rules() -> None:
    plan = compile_plan(product, references, platform, apparel, brand, mode="strict")
    assert [(item.slot, item.width, item.height) for item in plan.items] == [
        ("hero_front", 2000, 2000),
        ("detail_material", 1464, 600),
        ("detail_feature", 1464, 600),
    ]
    assert plan.pack_versions == {"platform": 1, "category": 1, "brand": 1}

def test_strict_plan_rejects_missing_required_view() -> None:
    with pytest.raises(PlanCompilationError, match="front reference"):
        compile_plan(product, [], platform, apparel, brand, mode="strict")
```

- [ ] **Step 2: Run tests and verify the compiler is missing**

Run: `uv run --project backend pytest backend/tests/templates/test_compiler.py -v`

- [ ] **Step 3: Implement pure deterministic compilation and persistence**

Merge rules in the order platform → category → brand, but allow only documented brand overrides (`palette`, `font`, `logo_asset_id`, and copy). Reject conflicting sizes, missing strict references, unsupported slots, or text outside declared regions. Persist the compiled snapshot and a stable SHA-256 compiler hash.

- [ ] **Step 4: Run compiler and API tests**

Run: `uv run --project backend pytest backend/tests/templates -v`

- [ ] **Step 5: Commit compiler work**

```bash
git add backend/src/aiimage/templates backend/alembic/versions/0007_production_plans.py backend/tests/templates
git commit -m "feat: compile versioned image production plans"
```

### Task 3: Multi-Image Plan Execution

**Files:**
- Modify: `backend/src/aiimage/workflow/models.py`
- Modify: `backend/src/aiimage/workflow/schemas.py`
- Modify: `backend/src/aiimage/workflow/service.py`
- Modify: `backend/src/aiimage/workflow/router.py`
- Create: `backend/alembic/versions/0008_link_batches_to_plans.py`
- Create: `backend/tests/workflow/test_production_plan.py`

**Interfaces:**
- Consumes: a persisted `ProductionPlan` and enabled `ModelConfiguration` supporting `reference_to_image`.
- Produces: `execute_production_plan(plan_id, model_configuration_id, actor_id) -> list[GenerationBatch]` and `POST /api/v1/production-plans/{id}/execute`.

- [ ] **Step 1: Write a failing atomic execution test**

```python
async def test_execute_plan_creates_one_batch_per_slot(session, plan, model, actor) -> None:
    batches = await execute_production_plan(session, plan.id, model.id, actor.id)
    assert [batch.requested_view for batch in batches] == [
        "hero_front", "detail_material", "detail_feature"
    ]
    assert {batch.production_plan_id for batch in batches} == {plan.id}
```

- [ ] **Step 2: Run the test and verify `execute_production_plan` is missing**

Run: `uv run --project backend pytest backend/tests/workflow/test_production_plan.py -v`

- [ ] **Step 3: Implement linked batch creation using existing queue and snapshots**

Create all batches and steps in one database transaction. Each batch snapshot stores the compiled plan hash, all pack versions, slot rules, reference hashes, and authoritative copy. Publish Redis hints only after the rows exist; failed hint delivery must not roll back authoritative state.

- [ ] **Step 4: Run workflow and recovery tests**

Run: `uv run --project backend pytest backend/tests/workflow backend/tests/worker backend/tests/recovery -v`

- [ ] **Step 5: Commit execution support**

```bash
git add backend/src/aiimage/workflow backend/alembic/versions/0008_link_batches_to_plans.py backend/tests/workflow
git commit -m "feat: execute multi-image production plans"
```

### Task 4: Deterministic Text Composition and Immutable Derivatives

**Files:**
- Create: `backend/src/aiimage/composition/__init__.py`
- Create: `backend/src/aiimage/composition/text.py`
- Create: `backend/src/aiimage/composition/service.py`
- Create: `backend/tests/composition/test_text.py`
- Create: `backend/tests/composition/test_service.py`
- Modify: `backend/src/aiimage/assets/models.py`
- Create: `backend/alembic/versions/0009_asset_derivations.py`

**Interfaces:**
- Consumes: immutable base image bytes and `TextLayer(text, region, font_size, color, align)` values from compiled plans.
- Produces: `render_text_layers(image, layers) -> bytes` and `create_composed_asset(...) -> Asset` with parent hash and operation parameters.

- [ ] **Step 1: Write failing pixel-size and provenance tests**

```python
def test_text_compositor_preserves_canvas_and_is_deterministic() -> None:
    first = render_text_layers(source_png, [layer])
    second = render_text_layers(source_png, [layer])
    assert first == second
    assert Image.open(BytesIO(first)).size == (1464, 600)

async def test_composed_asset_records_parent_and_operation(session) -> None:
    asset = await create_composed_asset(session, parent, [layer], actor_id)
    assert asset.parent_asset_id == parent.id
    assert asset.derivation_operation == "deterministic_text"
```

- [ ] **Step 2: Run tests and verify composition functions are missing**

Run: `uv run --project backend pytest backend/tests/composition -v`

- [ ] **Step 3: Implement safe deterministic Pillow rendering**

Use a bundled open-source font recorded in `THIRD_PARTY.md`, validate every bounding box against the declared platform text region, wrap without truncating authoritative values, and fail instead of silently shrinking below the pack minimum font size.

- [ ] **Step 4: Run asset and composition tests**

Run: `uv run --project backend pytest backend/tests/assets backend/tests/composition -v`

- [ ] **Step 5: Commit compositor work**

```bash
git add backend/src/aiimage/composition backend/src/aiimage/assets backend/alembic/versions/0009_asset_derivations.py backend/tests/composition THIRD_PARTY.md
git commit -m "feat: add deterministic commerce text layers"
```

### Task 5: Structural QA Evidence and Review Gate

**Files:**
- Create: `backend/src/aiimage/quality/__init__.py`
- Create: `backend/src/aiimage/quality/models.py`
- Create: `backend/src/aiimage/quality/schemas.py`
- Create: `backend/src/aiimage/quality/rules.py`
- Create: `backend/src/aiimage/quality/service.py`
- Create: `backend/src/aiimage/quality/router.py`
- Create: `backend/alembic/versions/0010_quality_results.py`
- Modify: `backend/src/aiimage/worker/executor.py`
- Modify: `backend/src/aiimage/review/service.py`
- Modify: `backend/src/aiimage/api/main.py`
- Test: `backend/tests/quality/test_rules.py`
- Test: `backend/tests/quality/test_review_gate.py`

**Interfaces:**
- Consumes: generated/composed asset metadata and compiled slot rules.
- Produces: append-only `QualityRun`/`QualityCheck` evidence and `GET /api/v1/batches/{id}/quality`; blocking failures prevent review approval.

- [ ] **Step 1: Write failing rule and review-gate tests**

```python
def test_wrong_dimensions_are_blocking() -> None:
    checks = inspect_structure(image_1024_square, rules={"width": 2000, "height": 2000})
    assert any(check.code == "dimensions" and check.blocking for check in checks)

async def test_batch_with_blocking_quality_failure_cannot_be_approved(session, batch, actor) -> None:
    await record_quality_failure(session, batch.id, code="dimensions", blocking=True)
    with pytest.raises(ReviewConflictError, match="blocking quality"):
        await decide_review(session, batch.id, actor.id, decision="approve")
```

- [ ] **Step 2: Run tests and verify quality modules are missing**

Run: `uv run --project backend pytest backend/tests/quality -v`

- [ ] **Step 3: Implement file and platform structural checks**

Check format, exact dimensions, aspect ratio, maximum bytes, alpha/background constraints when declared, and text-layer bounds. Persist measured values and expected values. Worker advances to `review_pending` only when no blocking check failed; failed batches remain inspectable with evidence.

- [ ] **Step 4: Run worker, quality, review, and export tests**

Run: `uv run --project backend pytest backend/tests/worker backend/tests/quality backend/tests/review backend/tests/export -v`

- [ ] **Step 5: Commit the quality gate**

```bash
git add backend/src/aiimage/quality backend/src/aiimage/worker backend/src/aiimage/review backend/alembic backend/tests/quality backend/src/aiimage/api/main.py
git commit -m "feat: gate reviews with structural quality evidence"
```

### Task 6: Operator UI for Pack Selection and Plan Preview

**Files:**
- Create: `apps/web/src/app/(authenticated)/production/new/page.tsx`
- Create: `apps/web/src/app/(authenticated)/production/[id]/page.tsx`
- Create: `apps/web/src/features/templates/production-form.tsx`
- Create: `apps/web/src/features/templates/plan-preview.tsx`
- Create: `apps/web/src/features/templates/production-form.test.tsx`
- Modify: `apps/web/src/components/app-shell.tsx`
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/app/(authenticated)/batches/[id]/page.tsx`

**Interfaces:**
- Consumes: template-pack listing, plan compile/execute, batch status, and quality-evidence APIs.
- Produces: a guided platform → brand → image-set preview → execute flow and visible per-slot QA evidence.

- [ ] **Step 1: Write a failing UI test for exact compiled slots**

```tsx
it("previews platform-derived slots before execution", async () => {
  render(<ProductionForm products={products} models={models} packs={packs} />)
  await user.selectOptions(screen.getByLabelText("目标平台"), "amazon-global")
  await user.click(screen.getByRole("button", { name: "编译图片套装" }))
  expect(await screen.findByText("正面主图 · 2000 × 2000")).toBeVisible()
  expect(screen.getByText("材质详情 · 1464 × 600")).toBeVisible()
})
```

- [ ] **Step 2: Run the test and verify the production form is missing**

Run: `pnpm --dir apps/web test -- production-form.test.tsx`

- [ ] **Step 3: Implement accessible form, preview, execution, and QA evidence**

Keep authoritative copy in explicit fields, mark rule values as platform defaults rather than certification, show the exact pack versions and strict-reference warnings before execution, and preserve the existing single-batch screen for direct generation.

- [ ] **Step 4: Run targeted frontend tests, lint, and build**

Run: `pnpm --dir apps/web test && pnpm --dir apps/web lint && pnpm --dir apps/web build`

- [ ] **Step 5: Commit the M2 operator flow**

```bash
git add apps/web
git commit -m "feat: add platform image-set production flow"
```

### Task 7: M2 Integration Verification and Documentation

**Files:**
- Create: `apps/web/e2e/m2-production-flow.spec.ts`
- Create: `scripts/verify-m2.sh`
- Modify: `README.md`
- Modify: `THIRD_PARTY.md`
- Modify: `docs/superpowers/plans/2026-08-17-m2-platform-rules-detail-images.md`

**Interfaces:**
- Consumes: all M2 backend and frontend features.
- Produces: one repeatable command that proves plan compilation, multi-slot generation, quality evidence, review, and platform export.

- [ ] **Step 1: Add a failing browser flow**

```ts
test("operator compiles and executes an Amazon apparel image set", async ({ page }) => {
  await loginAsLocalAdmin(page)
  await createProductWithFrontAndDetailReferences(page)
  await page.goto("/production/new")
  await page.getByLabel("目标平台").selectOption("amazon-global")
  await page.getByRole("button", { name: "编译图片套装" }).click()
  await expect(page.getByText("3 张图片")).toBeVisible()
  await page.getByRole("button", { name: "开始生成套图" }).click()
  await expect(page.getByText("结构质检通过").first()).toBeVisible()
})
```

- [ ] **Step 2: Implement the verification script**

`scripts/verify-m2.sh` must run Ruff, all backend tests, frontend lint/tests/build, `docker compose up -d --build --wait`, and both M1/M2 Playwright flows. It exits non-zero on any failure.

- [ ] **Step 3: Update boundaries and provenance documentation**

Document M2 as available, explicitly retain M3-M5 as unavailable, call the rule packs maintained defaults rather than official platform certification, and record any bundled font with fixed source and license.

- [ ] **Step 4: Run final verification**

Run: `bash scripts/verify-m2.sh`
Expected: backend checks/tests, frontend checks/tests/build, all containers, M1 E2E, and M2 E2E pass.

- [ ] **Step 5: Mark this plan complete and commit**

```bash
git add README.md THIRD_PARTY.md apps/web/e2e scripts/verify-m2.sh docs/superpowers/plans/2026-08-17-m2-platform-rules-detail-images.md
git commit -m "test: verify m2 platform image production"
```

## Plan Self-Review

- Spec coverage: M2 platform packs, apparel/category and brand composition, deterministic text, plan compilation, structural QA, review, and export are each assigned to a task.
- Scope exclusions: model assets, virtual try-on, cross-view consistency, mask editing, inpainting/outpainting, and later marketplace packs remain M3-M5.
- Type consistency: pack versions compile into `ProductionPlan`; plan items create linked `GenerationBatch` rows; quality evidence gates the existing review service.
- Placeholder scan: no implementation step depends on unspecified code or an undefined external service; exact production platform rule revalidation remains an explicit release boundary rather than fabricated evidence.
