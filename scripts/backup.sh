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
minio_container="$(docker compose ps -q minio)"
test -n "$minio_container"
docker run --rm --volumes-from "$minio_container" postgres:17-alpine \
  tar -C /data -cf - . > "$backup_dir/minio-$stamp.tar"
shasum -a 256 "$backup_dir/minio-$stamp.tar" > "$backup_dir/minio-$stamp.tar.sha256"
echo "$backup_dir/postgres-$stamp.dump"
echo "$backup_dir/minio-$stamp.tar"
echo "$backup_dir/minio-$stamp.tar.sha256"
