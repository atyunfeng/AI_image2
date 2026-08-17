# AI 电商自动化生图中台

面向国内外电商商品视觉生产的中台基础版本。M0–M1 已实现商品真值与多视角参考图、可配置模型 API KEY、持久化生成批次、后台 worker、结构化质量检查、人工审核、单图结果预览和带完整溯源清单的 ZIP 导出。

## 当前边界

当前版本完成商品主图/视角图的可靠生产闭环。详情页组合、局部微调/重绘、模特图、多角度一致性、虚拟试穿和各平台规则包已纳入后续 M2–M5 设计，不在本次 M1 中伪装成已上线能力。真实模型质量与 30 SKU 基准也必须由真实素材和用户提供的 API KEY 验证。

## 本地启动

要求 Docker Desktop、Python 3.13、uv、Node.js 22 和 pnpm 11。

```bash
cp .env.example .env
docker compose up -d --build --wait
```

- 中台：http://localhost:3000
- API 文档：http://localhost:8000/docs
- MinIO 控制台：http://localhost:9001
- 演示管理员：`admin@aiimage.local`
- 本地密码：`LocalOnly-ChangeMe-2026`

以上密钥只用于本地开发，部署前必须全部替换。

## 验证

```bash
bash scripts/verify-m0-m1.sh
```

脚本依次执行后端静态检查与测试、前端单测/检查/构建、Compose 健康检查和浏览器完整闭环。针对性命令：

```bash
uv run --project backend pytest backend/tests/worker backend/tests/review backend/tests/export -v
pnpm --dir apps/web test
pnpm --dir apps/web build
```

## 30 SKU 能力基准

把服装、鞋靴、帽饰各至少 10 个真实 SKU 素材按 `benchmarks/manifest.schema.json` 组织，再运行：

```bash
uv run --project backend aiimage-benchmark validate benchmarks/manifest.json
uv run --project backend aiimage-benchmark run benchmarks/manifest.json --model-configuration-id UUID
uv run --project backend aiimage-benchmark report benchmark-results.jsonl
```

仓库不包含虚构商品素材、真实供应商密钥或伪造的能力报告。

## 架构原则

PostgreSQL 是任务状态唯一事实源，Redis 只做唤醒提示，MinIO 保存内容寻址的不可变图片。worker 先提交租约再调用模型，重复投递不会重复执行已完成任务；Redis 短暂不可用时，恢复扫描仍可从 PostgreSQL 找回任务。所有导出都必须经过人工通过，并在 `manifest.json` 中记录 SKU、输入/输出哈希、真值版本、模型参数、成本和审核人。
