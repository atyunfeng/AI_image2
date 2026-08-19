#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: scripts/restore-check.sh postgres.dump minio.sha256" >&2
  exit 2
fi

pg_restore --list "$1" >/dev/null
test -s "$2"
echo "backup artifacts are readable; perform a disposable-environment restore before release"
