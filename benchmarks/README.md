# 30 SKU 模型能力基准

基准集至少包含服装、鞋靴、帽饰各 10 个 SKU。真实商品参考图不随源码分发；把素材放在 manifest 同级目录，填写相对路径和可选 SHA-256 后运行：

```bash
uv run --project backend aiimage-benchmark validate benchmarks/manifest.json
uv run --project backend aiimage-benchmark run benchmarks/manifest.json --model-configuration-id UUID
uv run --project backend aiimage-benchmark report benchmark-results.jsonl
```

`run` 只允许在已配置真实模型和真实素材的操作环境执行。本仓库不会伪造 30 SKU 素材、API KEY 或线上能力结论。
