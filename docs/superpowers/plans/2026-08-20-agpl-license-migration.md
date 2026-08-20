# AGPL-3.0-only License Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 AI_image2 的项目许可证从 `GPL-3.0-only` 一致迁移到 `AGPL-3.0-only`，并在 GitHub 上完成发布与许可证识别核验。

**Architecture:** 根目录 `LICENSE` 是许可证正文的唯一权威来源，包元数据只保存 SPDX 标识，README 与合规文档解释开源范围及网络交互场景的对应源码义务。第三方组件继续适用 `THIRD_PARTY.md` 中记录的独立许可证，不随根许可证迁移而改变。

**Tech Stack:** GNU AGPL v3、SPDX、Markdown、npm package metadata、Python `pyproject.toml`、Git、GitHub CLI

**Spec:** `docs/OPEN_SOURCE_SCOPE.md`

## Global Constraints

- 项目原创代码使用精确 SPDX 标识 `AGPL-3.0-only`。
- `LICENSE` 必须是 GNU 官方 AGPL v3 完整正文，不增加自定义限制。
- 不改变任何第三方组件的许可证声明。
- 修改版通过网络向用户提供交互服务时，必须显著提供该运行版本对应源码的访问方式。
- 本次不修改应用业务行为或模型接入逻辑。

---

### Task 1: Replace the authoritative license and metadata

**Files:**
- Modify: `LICENSE`
- Modify: `package.json`
- Modify: `apps/web/package.json`
- Modify: `backend/pyproject.toml`

**Interfaces:**
- Consumes: GNU 官方 `agpl-3.0.txt` 正文与 SPDX 标识 `AGPL-3.0-only`
- Produces: GitHub、npm 和 Python 工具可识别的一致许可证元数据

- [x] **Step 1: Replace the root license text**

使用 GNU 官方 `https://www.gnu.org/licenses/agpl-3.0.txt` 的完整正文替换 `LICENSE`。

- [x] **Step 2: Update package metadata**

将根 `package.json`、`apps/web/package.json` 和 `backend/pyproject.toml` 的许可证字段改为 `AGPL-3.0-only`。

- [x] **Step 3: Verify metadata parsing and license identity**

Run:

```bash
node -e "for (const file of ['package.json','apps/web/package.json']) { const value=require('./'+file).license; if (value !== 'AGPL-3.0-only') process.exit(1) }"
uv lock --project backend --check
head -n 2 LICENSE
```

Expected: JSON 与 Python 元数据检查通过，`LICENSE` 标题为 GNU AFFERO GENERAL PUBLIC LICENSE。

### Task 2: Update contributor and deployment guidance

**Files:**
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `NOTICE`
- Modify: `TRADEMARKS.md`
- Modify: `THIRD_PARTY.md`
- Modify: `apps/web/README.md`
- Modify: `docs/OPEN_SOURCE_SCOPE.md`
- Modify: `docs/RELEASING.md`

**Interfaces:**
- Consumes: 根目录 `LICENSE` 和 `AGPL-3.0-only` 元数据
- Produces: 贡献者、部署者和发布维护者可执行的许可证合规说明

- [x] **Step 1: Replace project-level GPL references**

将仅指向本项目根许可证的 `GPL-3.0-only`、GNU GPL v3 和“根目录 GPLv3”表述改为 AGPL 对应表述；保留 ComfyUI 等第三方条目原文。

- [x] **Step 2: Document network source obligations**

在 `README.md` 和 `docs/OPEN_SOURCE_SCOPE.md` 中说明：修改版通过网络提供交互服务时，应向远程用户显著提供运行版本的对应源码访问方式；在 `docs/RELEASING.md` 中加入部署核对项。

- [x] **Step 3: Scan for stale project-license references**

Run:

```bash
rg -n "\\bGPL-3\\.0-only|GNU General Public License|根目录 GPLv3|按 GPLv3" README.md CONTRIBUTING.md NOTICE TRADEMARKS.md THIRD_PARTY.md docs/OPEN_SOURCE_SCOPE.md docs/RELEASING.md package.json apps/web backend/pyproject.toml
```

Expected: 只允许第三方组件自身的 GPL 声明，不存在仍把项目根许可证描述为 GPL 的文本。

### Task 3: Validate, publish, and verify GitHub

**Files:**
- Test: all files changed by Tasks 1 and 2

**Interfaces:**
- Consumes: 完成迁移的功能分支提交
- Produces: `main` 与 `origin/main` 一致、GitHub 识别为 AGPL-3.0 的公开仓库

- [x] **Step 1: Run targeted repository checks**

Run:

```bash
git diff --check
node -e "JSON.parse(require('fs').readFileSync('package.json')); JSON.parse(require('fs').readFileSync('apps/web/package.json'))"
uv lock --project backend --check
```

Expected: 所有命令退出码为 0。

- [x] **Step 2: Commit the migration**

Run:

```bash
git add LICENSE README.md CONTRIBUTING.md NOTICE TRADEMARKS.md THIRD_PARTY.md package.json apps/web/package.json apps/web/README.md backend/pyproject.toml docs/OPEN_SOURCE_SCOPE.md docs/RELEASING.md docs/superpowers/plans/2026-08-20-agpl-license-migration.md
git commit -s -m "docs: switch project license to AGPLv3"
```

Expected: 功能分支产生一个包含 `Signed-off-by` 的许可证迁移提交。

- [x] **Step 3: Merge and push main**

Run:

```bash
git switch main
git merge --ff-only codex/agpl-license
git push origin main
```

Expected: `origin/main` 包含迁移提交。

- [x] **Step 4: Verify GitHub detection and clean the branch**

Run:

```bash
gh repo view atyunfeng/AI_image2 --json isPrivate,defaultBranchRef,licenseInfo,url
test "$(git rev-parse HEAD)" = "$(git ls-remote origin refs/heads/main | cut -f1)"
git branch -d codex/agpl-license
```

Expected: 仓库仍为公开，默认分支为 `main`，`licenseInfo.key` 为 `agpl-3.0`，本地与远程 SHA 一致，已合并功能分支被安全删除。
