# AI_image2 Web Console

AI_image2 的 Next.js 运营中台，提供商品、素材、套图生产、虚拟试穿、单图微调、批量任务、
审核、模板、模型配置和运营分析界面。

## 开发

请先按照仓库根目录 [README](../../README.md) 启动后端依赖，再执行：

```bash
pnpm install --frozen-lockfile
pnpm --dir apps/web dev
```

默认访问地址为 <http://localhost:3000>。浏览器只访问 Next.js 的同源 API 代理，不应直接
保存或回显模型 Provider API Key。

## 验证

```bash
pnpm --dir apps/web test
pnpm --dir apps/web lint
pnpm --dir apps/web build
```

端到端测试需要运行中的 Compose 环境，详见根目录验证脚本和贡献指南。

## License

本目录原创代码按 `AGPL-3.0-only` 发布，完整条款见仓库根目录 [LICENSE](../../LICENSE)。
