# M6 Full Product Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不包含真实模型供应商接入和首版明确非目标的前提下，补齐主产品规格中尚未实现的治理、商品真值、模板管理、生产控制、完整编辑图层、运营可观测性和导入导出功能。

**Architecture:** 延续 FastAPI 模块化单体、PostgreSQL 权威状态、Redis 唤醒、MinIO 不可变资产和 Next.js 运营后台。通过一份向前迁移增加软删除、编辑图层、导出记录和生产覆盖字段；新增 API 均由角色依赖保护并写入审计事件，前端继承现有深色高密度 Operate 界面。

**Tech Stack:** Python 3.13、FastAPI、SQLAlchemy 2、Alembic、PostgreSQL、Pillow、openpyxl、Next.js 16、React 19、TypeScript、Playwright

**Spec:** `docs/superpowers/specs/2026-08-17-ecommerce-ai-image-platform-design.md`

## Global Constraints

- 不实现首版非目标：自动发布、基础模型训练、Photoshop 级编辑、完整 ERP/PIM/DAM 替代和公众作品社区。
- 不伪造真实模型质量、平台官方认证、GPU 性能、30 SKU 通过率或供应商账单。
- 已审核或导出的资产保持不可变；业务删除使用软删除。
- API Key 不得出现在浏览器响应、普通日志、审计详情或任务快照。
- 新页面在 375、768、1024 和 1440 像素宽度可操作，宽表仅在自身容器内滚动。
- 每个新增敏感写操作必须保存 actor、事件类型、对象 ID 和非敏感变更摘要。

---

### Task 1: Administrator governance and audit console

**Files:**
- Create: `backend/src/aiimage/admin/router.py`
- Create: `backend/src/aiimage/admin/schemas.py`
- Create: `backend/src/aiimage/admin/service.py`
- Create: `backend/tests/admin/test_admin_api.py`
- Create: `apps/web/src/app/(authenticated)/admin/users/page.tsx`
- Create: `apps/web/src/app/(authenticated)/admin/audit/page.tsx`
- Create: `apps/web/src/features/admin/user-admin.tsx`
- Modify: `backend/src/aiimage/api/main.py`
- Modify: `apps/web/src/components/app-shell.tsx`
- Modify: `apps/web/src/lib/types.ts`

**Interfaces:**
- `GET /api/v1/admin/users` returns users without password hashes.
- `POST /api/v1/admin/users` creates a user with one or more roles.
- `PATCH /api/v1/admin/users/{id}` updates roles, active state or password while preventing the final active administrator from being disabled.
- `GET /api/v1/admin/audit` filters by event type, actor and date with newest-first pagination.

- [x] Write API tests proving admin-only access, redacted responses, lifecycle changes and final-admin protection.
- [x] Implement schemas and services using existing `create_user`, `hash_password` and `record_audit_event` functions.
- [x] Add the two admin pages with visible labels, inline feedback and responsive tables.
- [x] Run `uv run --project backend pytest backend/tests/admin -v` and targeted frontend tests.
- [x] Commit as `feat: add user governance and audit console`.

### Task 2: Product lifecycle, truth anchors, history and Excel import

**Files:**
- Create: `backend/alembic/versions/0018_product_completion.py`
- Modify: `backend/src/aiimage/catalog/models.py`
- Modify: `backend/src/aiimage/catalog/schemas.py`
- Modify: `backend/src/aiimage/catalog/service.py`
- Modify: `backend/src/aiimage/catalog/router.py`
- Create: `backend/tests/catalog/test_product_management.py`
- Modify: `backend/src/aiimage/bulk/service.py`
- Modify: `backend/src/aiimage/bulk/router.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/uv.lock`
- Create: `apps/web/src/features/products/product-management.tsx`
- Modify: `apps/web/src/app/(authenticated)/products/[id]/page.tsx`
- Modify: `apps/web/src/features/bulk/bulk-production.tsx`

**Interfaces:**
- `PATCH /products/{id}` updates name, category and brand; `DELETE /products/{id}` archives without deleting assets.
- `GET /products/{id}` includes latest truth anchor, all anchor versions and product history counters.
- `POST /products/{id}/truth-anchors/analyze` creates a deterministic image-metadata anchor version; `POST /products/{id}/truth-anchors` saves a manually confirmed document as a new immutable version.
- Bulk import accepts `.csv` and `.xlsx`, normalizes both into the existing row dictionary contract and preserves per-row isolation.

- [x] Add failing lifecycle, anchor-version and XLSX parsing tests.
- [x] Add soft-delete/brand fields and immutable truth-anchor services with Pillow color/size/reference analysis.
- [x] Add `openpyxl` and route CSV/XLSX by filename and MIME type.
- [x] Add product management and truth-anchor history UI; show generation, edit, review and export activity for the SKU.
- [x] Run catalog/bulk tests and commit as `feat: complete product truth management`.

### Task 3: Template pack authoring and immutable publishing

**Files:**
- Modify: `backend/src/aiimage/templates/models.py`
- Modify: `backend/src/aiimage/templates/schemas.py`
- Modify: `backend/src/aiimage/templates/service.py`
- Modify: `backend/src/aiimage/templates/router.py`
- Create: `backend/tests/templates/test_pack_management.py`
- Create: `apps/web/src/app/(authenticated)/templates/page.tsx`
- Create: `apps/web/src/features/templates/template-manager.tsx`
- Modify: `apps/web/src/components/app-shell.tsx`

**Interfaces:**
- `GET /template-packs/manage` returns every pack and version to admins/designers.
- `POST /template-packs` creates a pack with draft version 1.
- `POST /template-packs/{id}/versions` creates a draft copied from a selected immutable version or supplied JSON rules.
- `POST /template-pack-versions/{id}/publish` publishes one draft, preserving all historical versions.

- [x] Test role protection, unique slugs, immutable published rules and monotonically increasing versions.
- [x] Implement draft/published lifecycle without modifying existing preset versions.
- [x] Build the template center with kind filters, JSON validation, version history and composition preview links.
- [x] Run template tests and commit as `feat: add template version management`.

### Task 4: Per-image production controls, retry and parameter copy

**Files:**
- Modify: `backend/src/aiimage/templates/models.py`
- Modify: `backend/src/aiimage/templates/schemas.py`
- Modify: `backend/src/aiimage/templates/service.py`
- Modify: `backend/src/aiimage/templates/router.py`
- Modify: `backend/src/aiimage/workflow/schemas.py`
- Modify: `backend/src/aiimage/workflow/service.py`
- Modify: `backend/src/aiimage/workflow/router.py`
- Create: `backend/tests/workflow/test_production_controls.py`
- Modify: `apps/web/src/features/templates/plan-preview.tsx`
- Modify: `apps/web/src/features/templates/production-form.tsx`
- Create: `apps/web/src/features/batches/batch-actions.tsx`
- Modify: `apps/web/src/app/(authenticated)/batches/[id]/page.tsx`

**Interfaces:**
- `PATCH/DELETE /production-plans/{plan_id}/items/{item_id}` and `POST /production-plans/{plan_id}/items` edit only unexecuted plans.
- Each item can override model, dimensions, prompt, authoritative copy, reference IDs and provider parameters.
- `POST /batches/{id}/retry` creates a new traceable batch with the same inputs; `POST /batches/{id}/duplicate` accepts safe prompt/size/model overrides and records `source_batch_id`.

- [x] Add tests for unexecuted-only mutation, per-item model selection, strict references and retry provenance.
- [x] Implement item CRUD and batch cloning with new idempotency keys and audit records.
- [x] Add inline plan editing, add/remove controls, retry and copy-parameters actions.
- [x] Run workflow/template tests and commit as `feat: add per-image production controls`.

### Task 5: Automatic selection and full deterministic layer manager

**Files:**
- Modify: `backend/src/aiimage/editing/models.py`
- Modify: `backend/src/aiimage/editing/schemas.py`
- Modify: `backend/src/aiimage/editing/images.py`
- Modify: `backend/src/aiimage/editing/service.py`
- Modify: `backend/src/aiimage/editing/router.py`
- Create: `backend/tests/editing/test_layers.py`
- Create: `backend/tests/editing/test_segmentation.py`
- Create: `apps/web/src/features/editing/layer-manager.tsx`
- Modify: `apps/web/src/features/editing/edit-workspace.tsx`
- Modify: `apps/web/src/lib/types.ts`

**Interfaces:**
- `EditLayer` stores type, order, visibility, lock, opacity and type-specific content per revision.
- `POST /edit-projects/{id}/selections` returns an immutable mask for background or foreground/product using local pixel analysis; person/garment selection requires a configured `segment` provider and otherwise returns a clear 422 response.
- Layer create, update, duplicate, reorder and delete endpoints operate on a draft layer set and `POST /compose` materializes a new immutable revision.

- [ ] Test foreground/background masks, unsupported semantic selection, layer ordering/locking/visibility/opacity and deterministic composition.
- [ ] Implement local corner-color segmentation and persistent layer services.
- [ ] Replace the single text/logo form with a keyboard-accessible layer list and property editor while retaining existing revision history.
- [ ] Run editing tests and commit as `feat: complete selection and layer editing`.

### Task 6: Export records, operations metrics, filters and alerts

**Files:**
- Create: `backend/src/aiimage/export/models.py`
- Modify: `backend/src/aiimage/export/service.py`
- Modify: `backend/src/aiimage/export/router.py`
- Modify: `backend/src/aiimage/analytics/schemas.py`
- Modify: `backend/src/aiimage/analytics/service.py`
- Modify: `backend/src/aiimage/analytics/router.py`
- Create: `backend/tests/analytics/test_operations_report.py`
- Create: `backend/tests/export/test_export_history.py`
- Modify: `apps/web/src/app/(authenticated)/page.tsx`
- Modify: `apps/web/src/app/(authenticated)/analytics/page.tsx`
- Create: `apps/web/src/features/analytics/analytics-filters.tsx`

**Interfaces:**
- Every ZIP generation persists an `ExportRecord` with manifest hash, asset ID, actor and timestamp; repeated exports create records without overwriting prior files.
- `GET /analytics/operations` returns queue/review/failure counts, calls, success/retry rate, P50/P95 latency, cost groups, failure classes and actionable alert rows.
- Cost and operations pages expose date, Provider, platform, SKU and status filters without presenting estimates as settled bills.

- [ ] Test export immutability and operations percentile/failure/alert aggregation.
- [ ] Persist export archives as immutable assets and expose product/export history.
- [ ] Upgrade dashboard and analytics UI with filters, failure categories and retry links.
- [ ] Run analytics/export tests and commit as `feat: add operations observability and export history`.

### Task 7: Full-document verification and delivery

**Files:**
- Create: `apps/web/e2e/m6-full-product.spec.ts`
- Create: `scripts/verify-m6.sh`
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-08-17-ecommerce-ai-image-platform-design.md`
- Modify: `THIRD_PARTY.md`

**Interfaces:**
- The E2E flow creates a user, edits a product and truth anchor, authors/publishes a template version, adjusts a plan item, executes/retries one image, uses a deterministic selection/layer, reviews, exports and sees the audit/operations record.

- [ ] Add the full M6 Playwright flow and layout assertions for every new page.
- [ ] Run targeted tests during each task, then run `scripts/verify-m6.sh` across backend, frontend, build, Compose health and M1–M6 E2E.
- [ ] Run the UI detector once, capture desktop/mobile screenshots, perform the finish review and document remaining model-dependent release gates.
- [ ] Commit documentation, merge to `main`, verify merged `main`, push when a remote exists and clean merged branches only after remote containment is proven.
