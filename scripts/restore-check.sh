#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: scripts/restore-check.sh postgres.dump minio.tar minio.tar.sha256" >&2
  exit 2
fi

docker compose exec -T postgres pg_restore --list < "$1" >/dev/null
shasum -a 256 -c "$3"

restore_dir="$(mktemp -d)"
database_name="aiimage_restore_check_$(date -u +%Y%m%d%H%M%S)_$$"
cleanup() {
  docker compose exec -T postgres dropdb -U aiimage --if-exists "$database_name" >/dev/null 2>&1 || true
  rm -rf "$restore_dir"
}
trap cleanup EXIT

tar -xf "$2" -C "$restore_dir"
test -n "$(find "$restore_dir" -type f -print -quit)"
docker compose exec -T postgres createdb -U aiimage "$database_name"
docker compose exec -T postgres pg_restore -U aiimage -d "$database_name" < "$1"
docker compose exec -T postgres psql -U aiimage -d "$database_name" -Atc \
  "select count(*) from alembic_version" | grep -Eq '^[1-9][0-9]*$'
echo "PostgreSQL 与 MinIO 备份已在一次性目标中恢复并通过完整性检查"
