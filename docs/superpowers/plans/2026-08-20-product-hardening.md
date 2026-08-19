# AI 生图中台生产化收口 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute this plan task-by-task inline; subagents are not authorized for this run. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 修复生产阻断缺陷并补齐真实验收、可靠性、性能、安全和界面收口。

**Architecture:** 保持 Next.js + FastAPI 模块化单体、独立 Worker、PostgreSQL 权威状态、Redis 唤醒和 MinIO 不可变资产。新增能力沿现有模块边界实现，数据库迁移集中在一个版本，前端不吞掉权限和服务错误。

**Tech Stack:** Python 3.13、FastAPI、SQLAlchemy、PostgreSQL、Redis、S3/MinIO、Next.js 16、React 19、Vitest、Playwright。

**Spec:** `docs/superpowers/specs/2026-08-20-product-hardening-design.md`

## Global Constraints

- Mock 结果不得作为真实模型质量证据。
- 商品严格模式和人工最终放行保持不变。
- API Key 只在服务端以密文保存，任何响应和审计不得包含明文。
- PostgreSQL 是任务权威状态，Redis 只能作为可丢失的唤醒层。
- 不实现自动发布商品。

---

### Task 1: 权限闭环与错误语义

**Files:**
- Modify: `backend/src/aiimage/workflow/router.py`
- Modify: `apps/web/src/lib/api-client.ts`
- Modify: `apps/web/src/app/(authenticated)/review/page.tsx`
- Modify: `apps/web/src/components/app-shell.tsx`
- Test: `backend/tests/review/test_reviewer_access.py`
- Test: `apps/web/src/lib/api-client.test.ts`

**Interfaces:**
- Produces: role-safe bounded batch review queries, `ApiError`, role-aligned navigation.

- [x] 编写纯 reviewer 读取审核队列及禁止模型访问的失败测试。
- [x] 实现审核专用有界查询并复用批次响应转换。
- [x] 用 `ApiError` 区分 401、403、404、429、5xx，移除业务页面的静默空数据回退。
- [x] 对齐导航角色并添加页面级错误恢复。
- [x] 运行 review 后端测试与前端 API 客户端测试。

### Task 2: 模型配置生命周期与密钥治理

**Files:**
- Modify: `backend/src/aiimage/models/schemas.py`
- Modify: `backend/src/aiimage/models/service.py`
- Modify: `backend/src/aiimage/models/router.py`
- Modify: `apps/web/src/features/models/model-list.tsx`
- Test: `backend/tests/models/test_model_registry.py`
- Test: `apps/web/src/features/models/model-form.test.tsx`

**Interfaces:**
- Produces: `PATCH /api/v1/models/{id}`, write-only `api_key`, audited lifecycle events.

- [x] 编写更新、启停、轮换密钥和审计脱敏测试。
- [x] 实现 `ModelUpdate` 和服务端重新加密，空密钥保持旧值。
- [x] 为创建、更新、测试连接写入脱敏审计。
- [x] 在模型中心增加编辑、启停、测试和明确错误反馈。
- [x] 运行模型后端及前端针对性测试。

### Task 3: 可执行 Benchmark 与质量报告

**Files:**
- Modify: `backend/src/aiimage/benchmark/models.py`
- Modify: `backend/src/aiimage/benchmark/runner.py`
- Modify: `backend/src/aiimage/benchmark/report.py`
- Modify: `backend/src/aiimage/benchmark/cli.py`
- Test: `backend/tests/benchmark/test_runner.py`
- Test: `backend/tests/benchmark/test_report.py`

**Interfaces:**
- Produces: 真实 API 驱动的 `run_benchmark(...)`、逐次 JSONL、带发布门槛的 `CapabilityReport`。

- [x] 编写通过临时 API 服务执行清单并生成 JSONL 的失败测试。
- [x] 实现登录、素材创建、任务提交、轮询、证据读取和结果落盘。
- [x] 增加技术规则、人工试穿和分品类统计；缺少人工结果时保持未完成状态。
- [x] 验证无密钥、缺素材、超时和部分失败不会生成虚假通过。
- [x] 运行 benchmark 测试。

### Task 4: Worker 并发、重试与健康状态

**Files:**
- Modify: `backend/src/aiimage/config.py`
- Modify: `backend/src/aiimage/workflow/models.py`
- Modify: `backend/src/aiimage/workflow/queue.py`
- Modify: `backend/src/aiimage/worker/main.py`
- Modify: `backend/src/aiimage/worker/executor.py`
- Modify: `backend/src/aiimage/worker/recovery.py`
- Modify: `backend/src/aiimage/api/main.py`
- Create: `backend/alembic/versions/0019_product_hardening.py`
- Create: `backend/alembic/versions/0020_bulk_job_leases.py`
- Test: `backend/tests/worker/test_concurrency.py`
- Test: `backend/tests/worker/test_retry.py`
- Test: `backend/tests/api/test_health.py`

**Interfaces:**
- Produces: bounded consumer pool, `next_attempt_at`, retry limits, worker heartbeat, `/health/live`, `/health/ready`.

- [x] 编写并发上限、重试退避、恢复去重和依赖失败健康测试。
- [x] 增加任务调度字段和迁移。
- [x] 实现固定任务集合、错误分类和指数退避。
- [x] 实现 Redis TTL 去重唤醒与 Worker 心跳。
- [x] 实现 liveness/readiness 并接入 Compose。
- [x] 运行 worker、迁移和健康测试。

### Task 5: 有界查询和后台批量处理

**Files:**
- Modify: `backend/src/aiimage/catalog/router.py`
- Modify: `backend/src/aiimage/workflow/router.py`
- Modify: `backend/src/aiimage/bulk/router.py`
- Modify: `backend/src/aiimage/bulk/service.py`
- Modify: `backend/src/aiimage/analytics/service.py`
- Modify: `backend/src/aiimage/assets/router.py`
- Modify: `apps/web/src/features/batches/batch-list.tsx`
- Modify: relevant authenticated pages
- Test: relevant backend list and bulk tests

**Interfaces:**
- Produces: bounded `limit/offset` list APIs, batch latest-step join, queued bulk processing.

- [x] 编写默认上限、翻页稳定性和批量提交快速返回测试。
- [x] 将批次最新 Step 查询合并为单次 SQL。
- [x] 为主要列表增加上限和筛选，并保持旧响应兼容。
- [x] 把批量行处理移动到 Worker 可恢复任务。
- [x] 将运营汇总尽可能下推 SQL，并为资产响应增加条件请求支持。
- [x] 运行列表、批量和运营测试。

### Task 6: 平台规则与生产安全基线

**Files:**
- Modify: `backend/src/aiimage/templates/presets.py`
- Modify: `backend/src/aiimage/templates/schemas.py`
- Modify: `backend/src/aiimage/config.py`
- Modify: `backend/src/aiimage/providers/registry.py`
- Modify: `apps/web/next.config.ts`
- Modify: `backend/Dockerfile`
- Modify: `apps/web/Dockerfile`
- Modify: `docker-compose.yml`
- Create: `scripts/backup.sh`
- Create: `scripts/restore-check.sh`
- Create: `.github/workflows/ci.yml`
- Test: configuration and template tests

**Interfaces:**
- Produces: rule provenance metadata, production secret guard, egress validation, security headers and operational scripts.

- [x] 编写生产默认密钥拒绝、Provider URL 策略和规则元数据测试。
- [x] 增加生产配置校验与显式私网 Provider 开关。
- [x] 补齐规则来源、生效时间、适用区域和复核状态。
- [x] 配置安全响应头、非 root 容器、深度健康检查和资源限制。
- [x] 增加 CI、备份和恢复校验脚本。
- [x] 运行配置、模板、Compose config 和脚本静态检查。

### Task 7: 前端移动端、权限、可访问性和状态

**Files:**
- Modify: `apps/web/src/components/app-shell.tsx`
- Modify: `apps/web/src/app/globals.css`
- Modify: `apps/web/src/features/review/review-panel.tsx`
- Modify: `apps/web/src/features/editing/edit-workspace.tsx`
- Create: `apps/web/src/features/auth/logout-button.tsx`
- Create: `apps/web/src/components/service-state.tsx`
- Test: relevant Vitest and Playwright specs

**Interfaces:**
- Produces: mobile disclosure navigation, real readiness indicator, logout control, labelled review form and keyboard-safe editor guidance.

- [x] 编写角色导航、退出、审核标签和错误状态前端测试。
- [x] 实现移动端菜单、当前页状态、跳到主内容和退出登录。
- [x] 让系统状态读取 readiness，并提供不可用说明。
- [x] 补齐审核标签、动态播报、焦点样式和画布替代路径。
- [x] 运行 Vitest、ESLint、构建和一次 Impeccable detector。

### Task 8: 完整验收与收尾

**Files:**
- Modify: `README.md`
- Modify: `scripts/verify-m6.sh`
- Modify: `docs/superpowers/plans/2026-08-20-product-hardening.md`

**Interfaces:**
- Produces: 可重复的一键验证与明确外部发布门槛。

- [x] 更新部署、模型轮换、Benchmark、备份恢复和外部验收文档。
- [x] 运行后端完整测试与 Ruff。
- [x] 运行前端完整测试、ESLint、TypeScript 和生产构建。
- [x] 启动 Compose，检查迁移、readiness、MinIO、Worker 和 Playwright。
- [x] 生成 1440px 与 375px 截图，批量修复后最多复核一次。
- [x] 提交功能分支，合并 main，验证 main 并按仓库规则处理推送与分支清理。
