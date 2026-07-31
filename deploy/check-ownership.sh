#!/bin/sh
set -eu

deploy_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_root=${1:-$(CDPATH= cd -- "$deploy_dir/.." && pwd)}
env_file="$project_root/deploy/.env"

runtime_uid=$(
  sed -n 's/^KINKUDOS_UID=\([0-9][0-9]*\)$/\1/p' "$env_file" 2>/dev/null |
    tail -n 1
)
runtime_gid=$(
  sed -n 's/^KINKUDOS_GID=\([0-9][0-9]*\)$/\1/p' "$env_file" 2>/dev/null |
    tail -n 1
)
runtime_uid=${runtime_uid:-1000}
runtime_gid=${runtime_gid:-1000}

mismatches=$(
  find \
    "$project_root/data" \
    "$project_root/backups" \
    "$project_root/backup-state" \
    \( ! -uid "$runtime_uid" -o ! -gid "$runtime_gid" \) \
    -print 2>/dev/null |
    sed -n '1,20p'
)

if [ -n "$mismatches" ]; then
  echo "Runtime file ownership does not match KINKUDOS_UID:GID=$runtime_uid:$runtime_gid." >&2
  echo "$mismatches" >&2
  echo "Review the paths, then repair them explicitly with:" >&2
  echo "sudo chown -R $runtime_uid:$runtime_gid '$project_root/data' '$project_root/backups' '$project_root/backup-state'" >&2
  exit 1
fi
