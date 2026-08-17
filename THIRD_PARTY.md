# Third-Party Source Register

M0-M1 uses package dependencies through their published APIs. No upstream source files,
workflow JSON, model weights, branded assets, or UI media have been copied into this repository.

Architectural references only (no copied code):

- ComfyUI, https://github.com/Comfy-Org/ComfyUI, GPL-3.0: asynchronous graph execution and optional future local execution-node boundary.
- InvokeAI, https://github.com/invoke-ai/InvokeAI, Apache-2.0: canvas/gallery/workflow interaction research for later editing milestones.

The current implementation is original project code built on FastAPI, SQLAlchemy, Next.js,
React, Redis, PostgreSQL, MinIO/S3 and Pillow through their public package APIs.

Runtime font dependency:

- Noto Sans CJK, Debian package `fonts-noto-cjk`, SIL Open Font License 1.1: deterministic
  Chinese/Japanese/Korean text layers in containerized image composition. The package is
  installed from Debian Bookworm repositories; no font binary is committed to this repository.

Spreadsheet parsing dependency:

- openpyxl, MIT License: reads operator-supplied XLSX bulk-import workbooks. No upstream source
  file or workbook template is copied into this repository.

Before copying or modifying upstream source, record the repository URL, fixed commit, license,
copied paths, local destination, and modification summary here.
