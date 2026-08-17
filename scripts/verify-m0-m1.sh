#!/usr/bin/env bash
set -euo pipefail

docker compose config --quiet
uv run --project backend ruff check backend/src backend/tests
uv run --project backend pytest backend/tests -v
pnpm --dir apps/web lint
pnpm --dir apps/web test
pnpm --dir apps/web build
docker compose up -d --build --wait
pnpm --dir apps/web test:e2e
