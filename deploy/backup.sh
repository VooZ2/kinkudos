#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$project_dir"

docker compose exec -T app python manage.py backup_database --output-dir /app/backups
find "$project_dir/../backups" \
  -type f \
  -name 'kinkudos-*.sqlite3' \
  -mtime +31 \
  -delete
docker compose --profile backup run --rm restic backup /backups --tag kinkudos
docker compose --profile backup run --rm restic forget \
  --tag kinkudos \
  --keep-daily 31 \
  --prune
docker compose --profile backup run --rm restic check
