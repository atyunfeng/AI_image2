# AI 电商自动化生图中台

面向国内外电商商品视觉生产的中台。M0–M2 已实现商品真值与参考图、可配置模型 API KEY、持久化生成批次、后台 worker、人工审核和可追溯 ZIP 导出；新增淘宝/天猫、Amazon、TikTok Shop 首批规则包、服装品类包、品牌视觉包、三张套图编译执行、确定性文字层和逐图结构质检证据。

## 当前边界

当前版本完成商品主图与基础详情套图的可靠生产闭环。首批平台规则是中台维护的可追溯默认值，并非平台官方认证，正式上架前必须按目标站点最新政策复核。局部微调/重绘、模特图、跨视角一致性、虚拟试穿和更多平台规则已纳入后续 M3–M5，不在本次 M2 中伪装成已上线能力。真实模型质量与 30 SKU 基准也必须由真实素材和用户提供的 API KEY 验证。

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
bash scripts/verify-m2.sh
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
