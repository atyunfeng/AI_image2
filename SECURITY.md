# Security Policy

## 支持范围

安全修复面向 `main` 和最新 GitHub Release。旧版本可能需要先升级后才能获得修复。

## 私下报告漏洞

请使用 GitHub 仓库 **Security → Report a vulnerability** 提交私密漏洞报告，不要公开
创建 Issue、Discussion 或 Pull Request。报告中请包含：

- 受影响版本或提交；
- 可复现步骤和最小验证材料；
- 可能影响的数据、权限和部署范围；
- 已尝试的缓解措施；
- 是否已经在其他渠道披露。

维护者会尽快确认报告并协商修复与披露时间。请在公开漏洞细节前给维护者合理的修复窗口。

## 部署方责任

生产环境必须替换 `.env.example` 和 `docker-compose.yml` 中的全部本地示例密钥，关闭
非必要的私网 Provider URL，限制 MinIO、PostgreSQL 和 Redis 的网络访问，并定期轮换
模型 Provider API Key。模型 Key 不应写入日志、Issue、截图或导出文件。
