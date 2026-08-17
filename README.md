# AI 电商自动化生图中台

面向国内外电商商品视觉生产的中台。M0–M6 已实现商品真值与参考图、可配置模型 API KEY、持久化生成批次、后台 worker、人工审核和可追溯 ZIP 导出；覆盖 11 个国内外平台默认规则包、服装鞋帽的授权模特、多角度和虚拟试穿、不可变单图微调、CSV/XLSX 批量生产、模板版本、用户治理、审计和运营告警。

## 当前边界

当前版本完成商品主图、基础详情套图，以及服装、鞋帽的商品图、授权模特图、正侧背多角度和虚拟试穿编排。严格模式缺少对应商品侧面或背面参考时会阻止任务，创意模式会记录推断标记；人体结构、服饰穿插、模特身份和跨视角一致性仍必须人工复核。

单图微调支持画笔/擦除/反选、蒙版膨胀与羽化、局部替换与消除、换背景、扩图，以及商品/背景确定性自动选择。人物和服装语义选择要求配置 `segment` 模型。持久化图层支持显隐、锁定、不透明度、复制、排序、删除和合成；每次合成都是独立派生版本并重新进入审核。

平台规则覆盖淘宝/天猫、京东、拼多多、抖音电商、Amazon、TikTok Shop、Shopify、Temu、Shopee、Lazada 和 eBay。它们是中台维护的可追溯默认值，并非平台官方认证，上架前必须复核目标站点的最新规则。

批量生产接受 UTF-8 CSV 或 XLSX，必填列为 `sku,name,category,platform_slug`，可选列为 `brand,mode,reference_asset_id,reference_view`。已有 SKU 可以复用中台参考图；新 SKU 或无图 SKU 必须填写已上传图片的资产 ID。每行独立记录结果，错误 CSV 可单独下载。

成本运营按模型配置的三位币种分组，只展示 Provider 回传或配置估算值，不替代服务商账单。运营报告提供队列、成功/重试率、P50/P95 延迟、失败分类和积压告警，并支持日期、Provider、平台、SKU、状态筛选。全局和 Provider 并发上限通过 `AIIMAGE_WORKER_MAX_CONCURRENCY` 与 `AIIMAGE_PROVIDER_CONCURRENCY_LIMITS` 设置。

Mock Provider 只验证任务编排、证据和审核闭环，不代表真实试穿、重绘或上架质量。真实模型、30 SKU 基准、主图技术规则 90% 通过率及虚拟试穿 80% 人工通过率必须使用真实素材和用户提供的 API KEY 验证；自动发布商品仍不在当前范围内。

## 本地启动

要求 Docker Desktop、Python 3.13、uv、Node.js 22 和 pnpm 11。

```bash
cp .env.example .env
docker compose up -d --build --wait
```

- 中台：http://localhost:3000
- 中台管理员：`admin@aiimage.local`
- 中台密码：`LocalOnly-ChangeMe-2026`
- API 文档：http://localhost:8000/docs
- MinIO 控制台：http://localhost:9001
- MinIO 根账号：`aiimage`
- MinIO 根密码：`local-development-secret`

以上密钥只用于本地开发，部署前必须全部替换。

## 验证

```bash
bash scripts/verify-m0-m1.sh
bash scripts/verify-m2.sh
bash scripts/verify-m3.sh
bash scripts/verify-m4.sh
bash scripts/verify-m5.sh
bash scripts/verify-m6.sh
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

PostgreSQL 是任务状态唯一事实源，Redis 只做唤醒提示，MinIO 保存内容寻址的不可变商品、模特、蒙版、生成图片和导出压缩包。worker 先提交租约再调用模型，重复投递不会重复执行已完成任务；Redis 短暂不可用时，恢复扫描仍可从 PostgreSQL 找回任务。每次重试、参数复制、模板发布、真值变更、图层编辑和导出都保留来源或审计记录。所有导出都必须经过人工通过，并在 `manifest.json` 中记录 SKU、输入/输出哈希、真值版本、模型参数、成本和审核人。
