# Third-Party Source and License Register

本项目通过已发布的软件包、容器镜像和标准协议使用第三方组件。除锁文件和许可证要求的
通知外，仓库没有提交上游源文件、工作流 JSON、模型权重、品牌素材或第三方 UI 媒体。
第三方组件继续适用其各自许可证，根目录 AGPLv3 不会替换这些许可证。

## 架构参考（未复制代码）

- ComfyUI, https://github.com/Comfy-Org/ComfyUI, GPL-3.0: asynchronous graph execution and optional future local execution-node boundary.
- InvokeAI, https://github.com/invoke-ai/InvokeAI, Apache-2.0: canvas/gallery/workflow interaction research for later editing milestones.

## 直接软件包依赖

前端直接依赖 Next.js、React、TanStack Query 和 Zod；后端直接依赖 FastAPI、SQLAlchemy、
Alembic、asyncpg、boto3、Redis Python client、Pillow、openpyxl、cryptography、PyJWT、
HTTPX、Pydantic 和 Uvicorn 等。锁定版本分别记录在 `pnpm-lock.yaml` 和
`backend/uv.lock`。

当前依赖清单检测到的许可证族包括 MIT、MIT-0、Apache-2.0、BSD-2-Clause、
BSD-3-Clause、ISC、0BSD、BlueOak-1.0.0、MPL-2.0、LGPL-3.0-or-later、Python-2.0、
CC0-1.0 和 CC-BY-4.0。发布二进制或容器镜像时必须保留相应版权与许可证通知。

可用以下命令按当前锁文件重新生成依赖清单：

```bash
pnpm licenses list --json
uv run --project backend python - <<'PY'
from importlib.metadata import distributions

for distribution in sorted(distributions(), key=lambda item: item.metadata["Name"].lower()):
    license_name = (
        distribution.metadata.get("License-Expression")
        or distribution.metadata.get("License")
        or "UNKNOWN"
    )
    print(distribution.metadata["Name"], distribution.version, license_name, sep="\t")
PY
```

## 运行时服务与基础镜像

- PostgreSQL 17 Alpine image: PostgreSQL License.
- Redis 8 Alpine image: this project selects the AGPLv3 option offered for Redis 8 Open Source.
- MinIO pinned server image: GNU AGPLv3 unless the deployer obtains a commercial license.
- Python 3.13 slim Bookworm image and Node.js 22 Alpine image: their included components retain
  their individual notices and licenses.

## 字体

- Noto Sans CJK, Debian package `fonts-noto-cjk`, SIL Open Font License 1.1: deterministic
  Chinese/Japanese/Korean text layers in containerized image composition. The package is
  installed from Debian Bookworm repositories; no font binary is committed to this repository.

## 表格解析

- openpyxl, MIT License: reads operator-supplied XLSX bulk-import workbooks. No upstream source
  file or workbook template is copied into this repository.

复制或修改任何上游源代码前，必须在这里登记仓库 URL、固定提交、许可证、复制路径、
本地目标和修改摘要。仅写“参考”不能替代许可证核验。
