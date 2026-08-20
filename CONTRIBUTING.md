# Contributing to AI_image2

感谢你参与 AI_image2。提交贡献即表示你同意贡献内容按本仓库的
`AGPL-3.0-only` 许可证发布，并确认你有权提交这些内容。

## 开始之前

- 安全漏洞请按 [SECURITY.md](SECURITY.md) 私下报告，不要创建公开 Issue。
- 功能建议先创建 Issue，说明使用场景、预期行为和验收方式。
- 不要提交真实 API Key、商品隐私数据、未授权人物素材、模型权重或第三方品牌素材。
- 第三方代码或工作流必须记录固定版本、许可证、来源和本地修改，详见
  [THIRD_PARTY.md](THIRD_PARTY.md)。

## 本地开发

项目要求 Docker Desktop、Python 3.13、uv、Node.js 22 和 pnpm 11。

```bash
cp .env.example .env
uv sync --project backend --frozen
pnpm install --frozen-lockfile
```

提交前至少运行与你改动直接相关的检查。跨前后端或共享基础设施改动应运行：

```bash
uv run --project backend ruff check backend/src backend/tests
uv run --project backend pytest backend/tests
pnpm --dir apps/web lint
pnpm --dir apps/web test
pnpm --dir apps/web build
```

## 提交和 Pull Request

- 从最新 `main` 创建范围明确的分支。
- 一个 Pull Request 只处理一个主题，避免无关重构和格式化。
- 说明行为变化、测试证据、风险和仍需人工验证的边界。
- UI 改动附上桌面端和移动端截图；不要在截图中暴露业务数据或凭据。
- 不得把 Mock Provider 或模拟结果描述为真实模型质量验收。

本项目使用 [Developer Certificate of Origin 1.1](https://developercertificate.org/)；
每个提交必须带有签署行：

```bash
git commit -s -m "fix: describe the change"
```

`Signed-off-by` 表示你确认有权按本项目许可证提交该贡献。
