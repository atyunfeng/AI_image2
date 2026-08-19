#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: scripts/backup.sh /absolute/backup-directory" >&2
  exit 2
fi

backup_dir="$1"
case "$backup_dir" in
  /*) ;;
  *) echo "backup directory must be absolute" >&2; exit 2 ;;
esac
mkdir -p "$backup_dir"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
docker compose exec -T postgres pg_dump -U aiimage -Fc aiimage > "$backup_dir/postgres-$stamp.dump"
docker compose exec -T minio sh -c 'find /data -type f -print0 | sort -z | xargs -0 sha256sum' > "$backup_dir/minio-$stamp.sha256"
echo "$backup_dir/postgres-$stamp.dump"
echo "$backup_dir/minio-$stamp.sha256"
