# M3 Fashion Model, Multi-Angle, and Virtual Try-On Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add authorized system/brand model assets and a durable apparel, shoes, and hats workflow that generates product-on-model, multi-angle, detail, and virtual-try-on outputs without weakening strict product-reference rules.

**Architecture:** Add a `talent` domain for model profiles, authorization metadata, and immutable multi-view references. Extend the existing generation batch with an explicit provider capability and optional model profile, then add a `fashion` compiler that validates product/model reference coverage and atomically creates specialized batches through the existing PostgreSQL/Redis/worker pipeline. The worker supplies product and model references to capability-aware provider adapters and stores M3 verification evidence before human review.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy 2, Alembic, PostgreSQL 17, Redis 8, MinIO/S3, Pillow, Next.js 16, React 19, TypeScript 5.9, pytest, Vitest, Playwright, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-08-17-ecommerce-ai-image-platform-design.md`

**Implementation status:** Completed on `feat/m3-fashion-model-tryon`. Full local verification covers Ruff, 54 backend tests, 7 frontend tests, lint, production build, healthy Docker Compose services, and M1/M2/M3 Playwright flows. Mock Provider proves orchestration only; real-provider quality gates remain open.

## Global Constraints

- This plan covers M3 only: system/brand model profiles, model references, specialized fashion plans, multi-angle, virtual try-on, strict-reference validation, and M3 review evidence.
- M4 mask editing, inpainting, outpainting, transform controls, layers, undo/redo, and edit branches remain separate.
- A brand/real-person model profile cannot be selected unless its authorization status is `valid` and its expiry date has not passed.
- Strict mode requires a matching product reference for front, side, and back outputs; creative mode may infer missing views but must remain labeled `ai_completed` in snapshots and review UI.
- Virtual try-on requires an enabled provider configuration advertising `virtual_try_on`; multi-angle outputs require `multi_reference_to_image`.
- Model references and product references remain separate immutable assets with independent provenance.
- Automated checks may verify inputs and file structure, but anatomy, garment penetration, identity, and cross-view consistency remain mandatory human review evidence unless a configured visual QA provider returns measurements.
- Real provider quality and the 80% virtual-try-on acceptance gate require user-supplied assets/API keys and are not fabricated by Mock Provider tests.
- Use targeted tests per task; run `bash scripts/verify-m3.sh` only after integration.

---

### Task 1: Authorized Model Profile Domain

**Files:**
- Create: `backend/src/aiimage/talent/{__init__,models,schemas,service,router}.py`
- Create: `backend/alembic/versions/0011_model_profiles.py`
- Modify: `backend/src/aiimage/api/main.py`
- Modify: `backend/alembic/env.py`
- Modify: `backend/tests/conftest.py`
- Test: `backend/tests/talent/test_model_profiles.py`

**Interfaces:**
- Produces: `ModelProfile`, `ModelReference`, `POST/GET /api/v1/model-profiles`, and `POST /api/v1/model-profiles/{id}/references`.

- [ ] Write tests proving system models can be active without a portrait authorization document, brand models require authorization status/expiry, saved assets are immutable, and expired profiles are not selectable.
- [ ] Implement profile types `system_virtual` and `brand_authorized`, authorization states `not_required`, `valid`, `expired`, and reference views `front`, `side`, `back`, `half_body`, `full_body`.
- [ ] Store structured appearance tags without protected-attribute inference; accept only operator-provided labels.
- [ ] Run `uv run --project backend pytest backend/tests/talent -v` and commit `feat: add authorized model profiles`.

### Task 2: Capability-Aware Fashion Plan Compiler

**Files:**
- Create: `backend/src/aiimage/fashion/{__init__,schemas,compiler,service,router}.py`
- Modify: `backend/src/aiimage/workflow/models.py`
- Modify: `backend/src/aiimage/workflow/schemas.py`
- Create: `backend/alembic/versions/0012_fashion_batches.py`
- Test: `backend/tests/fashion/test_compiler.py`
- Test: `backend/tests/fashion/test_api.py`

**Interfaces:**
- Produces: `compile_fashion_plan(category, requested_outputs, product_views, model_views, mode)` and `POST /api/v1/fashion-plans` returning linked `GenerationBatch` rows.

- [ ] Write compiler tests for apparel/shoes/hats slot routing, missing side/back strict failures, creative `ai_completed` labels, expired-model rejection, and capability mismatch rejection.
- [ ] Add nullable `model_profile_id`, required `capability` defaulting to `reference_to_image`, and `fashion_plan_id` to generation batches.
- [ ] Implement outputs `product_front`, `model_front`, `model_side`, `model_back`, `detail`, and `virtual_try_on`; route model angles to `multi_reference_to_image` and try-on to `virtual_try_on`.
- [ ] Atomically persist one batch/step per output with product/model reference IDs, authorization snapshot, inferred-view marker, and requested pose.
- [ ] Run fashion/workflow/recovery tests and commit `feat: compile specialized fashion generation plans`.

### Task 3: Worker Provider Inputs and M3 Evidence

**Files:**
- Modify: `backend/src/aiimage/worker/executor.py`
- Modify: `backend/src/aiimage/models/domain.py`
- Modify: `backend/src/aiimage/providers/mock.py`
- Create: `backend/src/aiimage/fashion/evidence.py`
- Create: `backend/src/aiimage/fashion/models.py`
- Create: `backend/alembic/versions/0013_fashion_evidence.py`
- Test: `backend/tests/worker/test_fashion_executor.py`
- Test: `backend/tests/fashion/test_evidence.py`

**Interfaces:**
- Consumes: capability and separate product/model reference IDs from batch snapshots.
- Produces: capability-correct `GenerationRequest`, immutable output, and append-only `FashionEvidence` rows.

- [ ] Write tests that virtual try-on receives both garment and model references, multi-angle receives ordered multi-reference inputs, and duplicate deliveries remain no-ops.
- [ ] Persist checks for authorization snapshot, required input views, output dimensions, inferred-view labeling, and required human-review categories.
- [ ] Make provider errors retain capability/request IDs without logging image bytes or API keys.
- [ ] Run worker/provider/fashion tests and commit `feat: execute virtual try-on and multi-angle jobs`.

### Task 4: Model Center and Fashion Generation UI

**Files:**
- Create: `apps/web/src/app/(authenticated)/talent/{page,new/page}.tsx`
- Create: `apps/web/src/app/(authenticated)/fashion/{new/page,[id]/page}.tsx`
- Create: `apps/web/src/features/talent/{model-form,reference-upload,model-list}.tsx`
- Create: `apps/web/src/features/fashion/{fashion-form,fashion-results,evidence-panel}.tsx`
- Modify: `apps/web/src/components/app-shell.tsx`
- Modify: `apps/web/src/lib/types.ts`
- Test: `apps/web/src/features/fashion/fashion-form.test.tsx`

**Interfaces:**
- Consumes: model-profile, fashion-plan, batch, asset, evidence, and review APIs.
- Produces: model authorization/reference management and guided product + model + outputs + strict/creative generation flow.

- [ ] Write a UI test proving strict mode exposes front/side/back selection, capability-aware model filtering, and authorization warnings.
- [ ] Implement visible labels, busy states, inline API errors, keyboard-safe controls, exact capability explanation, and no misleading claim that Mock output is production-quality try-on.
- [ ] Show generated angles independently with their inferred marker, provider capability, review link, and mandatory anatomy/identity/garment checks.
- [ ] Run frontend tests, lint, and build; commit `feat: add fashion model and try-on workspace`.

### Task 5: M3 Browser Verification and Main-Branch Delivery

**Files:**
- Create: `apps/web/e2e/m3-fashion-flow.spec.ts`
- Create: `scripts/verify-m3.sh`
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-08-17-ecommerce-ai-image-platform-design.md`

**Interfaces:**
- Produces: repeatable proof of model creation → model reference upload → garment references → virtual try-on/multi-angle generation → evidence → review/export.

- [ ] Add an E2E using Mock Provider configured with `reference_to_image`, `multi_reference_to_image`, and `virtual_try_on`.
- [ ] Verify strict mode rejects a requested missing view, then upload front/side/back references and complete all requested outputs.
- [ ] Make `scripts/verify-m3.sh` run Ruff, all backend tests, frontend lint/tests/build, Compose health, and M1/M2/M3 Playwright flows.
- [ ] Update documentation to mark M3 available while preserving the real-provider/30-SKU/80%-acceptance release gates.
- [ ] Merge only after the feature branch and merged `main` both pass `bash scripts/verify-m3.sh`.

## Self-Review

- M3 coverage is complete across authorized models, model references, category-specific compilation, provider capabilities, multi-angle/try-on execution, evidence, review, UI, and E2E.
- M4 editing and M5 platform/GPU expansion remain excluded.
- Strict and creative modes have explicit, testable differences; no missing product angle is silently presented as factual.
- Mock Provider proves orchestration only and cannot satisfy real visual-quality release gates.
