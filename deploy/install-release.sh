#!/bin/sh
set -eu

archive=${1:-}
checksum_file=${2:-}
version=${3:-}
project_root=${4:-}

if [ -z "$archive" ] || [ -z "$checksum_file" ] || [ -z "$version" ] || [ -z "$project_root" ]; then
  echo "Usage: install-release.sh ARCHIVE SHA256_FILE VERSION PROJECT_ROOT" >&2
  exit 2
fi

case "$version" in
  *[!0-9.]*|.*|*..*|*.) echo "Invalid release version: $version" >&2; exit 2 ;;
esac

image_tag=${KINKUDOS_IMAGE_TAG:-$version}
case "$image_tag" in
  ""|*[!0-9A-Za-z._-]*) echo "Invalid Docker image tag: $image_tag" >&2; exit 2 ;;
esac
export KINKUDOS_IMAGE_TAG="$image_tag"

image_repository=${KINKUDOS_IMAGE_REPOSITORY:-vooz2/kinkudos}
case "$image_repository" in
  ""|*[!0-9A-Za-z._/-]*|/*|*/|*//* ) echo "Invalid Docker image repository: $image_repository" >&2; exit 2 ;;
esac
export KINKUDOS_IMAGE_REPOSITORY="$image_repository"

archive=$(realpath "$archive")
checksum_file=$(realpath "$checksum_file")
project_root=$(realpath "$project_root")
deploy_dir="$project_root/deploy"
secrets_dir="$project_root/secrets"
releases_dir="$project_root/releases"
release_dir="$releases_dir/$version"
staging_dir="$releases_dir/.staging-$version-$$"
image="$image_repository:$image_tag"
container="kinkudos-app-1"

test -f "$archive"
test -f "$checksum_file"
test -d "$deploy_dir"
test -f "$deploy_dir/compose.yml"

if [ -f "$project_root/install-profile" ]; then
  echo "Unsupported installation profile: $(cat "$project_root/install-profile")" >&2
  exit 1
fi

umask 077
mkdir -p \
  "$secrets_dir/backup" \
  "$secrets_dir/smtp" \
  "$project_root/data" \
  "$project_root/backups" \
  "$project_root/backup-state"

protect_directory() {
  if [ -L "$1" ] || [ ! -d "$1" ]; then
    echo "Expected a real KinKudos directory: $1" >&2
    exit 1
  fi
  chmod 0700 "$1"
}

protect_directory "$secrets_dir/backup"
protect_directory "$secrets_dir/smtp"
protect_directory "$project_root/backups"
protect_directory "$project_root/backup-state"
for backup_file in "$project_root/backups"/kinkudos-*.sqlite3; do
  if [ -f "$backup_file" ] && [ ! -L "$backup_file" ]; then
    chmod 0600 "$backup_file"
  fi
done

if [ ! -s "$secrets_dir/backup_agent_token" ]; then
  openssl rand -base64 48 | tr -d '\n' > "$secrets_dir/backup_agent_token"
fi
if [ ! -s "$secrets_dir/setup_token" ]; then
  openssl rand -base64 36 | tr -d '\n' > "$secrets_dir/setup_token"
fi
if [ ! -s "$secrets_dir/restic_password" ]; then
  openssl rand -base64 48 | tr -d '\n' > "$secrets_dir/restic_password"
fi
if [ ! -f "$secrets_dir/backup/restic.env" ] && [ -f "$secrets_dir/restic.env" ]; then
  cp "$secrets_dir/restic.env" "$secrets_dir/backup/restic.env"
fi
if [ ! -f "$secrets_dir/backup/restic.env" ]; then
  {
    echo "# Choose any repository type supported by restic."
    echo "RESTIC_REPOSITORY=REPLACE_WITH_REPOSITORY"
  } > "$secrets_dir/backup/restic.env"
fi
chmod 0600 \
  "$secrets_dir/backup_agent_token" \
  "$secrets_dir/setup_token" \
  "$secrets_dir/restic_password" \
  "$secrets_dir/backup/restic.env"

runtime_uid=$(
  sed -n 's/^KINKUDOS_UID=\([0-9][0-9]*\)$/\1/p' "$deploy_dir/.env" 2>/dev/null |
    tail -n 1
)
runtime_gid=$(
  sed -n 's/^KINKUDOS_GID=\([0-9][0-9]*\)$/\1/p' "$deploy_dir/.env" 2>/dev/null |
    tail -n 1
)
runtime_uid=${runtime_uid:-${SUDO_UID:-$(id -u)}}
runtime_gid=${runtime_gid:-${SUDO_GID:-$(id -g)}}
chown "$runtime_uid:$runtime_gid" \
  "$project_root/backups" \
  "$project_root/backup-state" \
  "$secrets_dir/backup" \
  "$secrets_dir/smtp" \
  "$secrets_dir/backup_agent_token" \
  "$secrets_dir/setup_token" \
  "$secrets_dir/restic_password" \
  "$secrets_dir/backup/restic.env"

expected_checksum=$(awk 'NR == 1 {print $1}' "$checksum_file")
actual_checksum=$(sha256sum "$archive" | awk '{print $1}')
if [ "$actual_checksum" != "$expected_checksum" ]; then
  echo "Release checksum does not match." >&2
  exit 1
fi

mkdir -p "$releases_dir"
rm -rf -- "$staging_dir"
mkdir "$staging_dir"
cleanup() {
  rm -rf -- "$staging_dir"
}
trap cleanup EXIT INT TERM

python3 - "$archive" <<'PY'
import sys
import tarfile
from pathlib import PurePosixPath

with tarfile.open(sys.argv[1], "r:gz") as archive:
    for member in archive.getmembers():
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts or member.issym() or member.islnk():
            raise SystemExit(f"Unsafe archive member: {member.name}")
PY

tar -xzf "$archive" --strip-components=1 -C "$staging_dir"

release_version=$(
  sed -n 's/^version = "\([^"]*\)"$/\1/p' "$staging_dir/pyproject.toml" | head -n 1
)
if [ "$release_version" != "$version" ]; then
  echo "Archive version $release_version does not match requested version $version." >&2
  exit 1
fi

python3 "$staging_dir/scripts/verify_release.py"

docker pull "$image"

docker run --rm \
  --network none \
  --entrypoint /bin/sh \
  --env KINKUDOS_DEBUG=true \
  --env KINKUDOS_DATABASE_PATH=/tmp/kinkudos-smoke.sqlite3 \
  "$image" \
  -c 'python scripts/verify_release.py &&
      python manage.py migrate --noinput &&
      python manage.py check'

cd "$deploy_dir"
if [ ! -f "$deploy_dir/compose.override.yml" ]; then
  cp "$staging_dir/deploy/compose.traefik.yml" "$deploy_dir/compose.override.yml"
  echo "Created compose.override.yml for the existing Traefik deployment."
fi
"$staging_dir/deploy/check-ownership.sh" "$project_root"
docker compose config --quiet
if ! docker compose config --images | grep -Fx "$image" >/dev/null; then
  echo "Compose does not reference the release image $image." >&2
  exit 1
fi

docker compose exec -T app \
  python manage.py backup_database --output-dir /app/backups

rm -rf -- "$release_dir"
mv "$staging_dir" "$release_dir"
trap - EXIT INT TERM

if ! docker compose up -d --no-build --force-recreate app backup-agent; then
  echo "Could not start KinKudos $version." >&2
  exit 1
fi

healthy=false
attempt=0
while [ "$attempt" -lt 60 ]; do
  status=$(
    docker inspect "$container" \
      --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
      2>/dev/null || true
  )
  if [ "$status" = "healthy" ]; then
    healthy=true
    break
  fi
  attempt=$((attempt + 1))
  sleep 2
done

if [ "$healthy" != "true" ]; then
  docker compose logs --tail=100 app >&2 || true
  echo "Health check failed; the database may contain migrations from $version." >&2
  echo "The previous image was not restored automatically. Resolve the release compatibility issue before restarting an older image." >&2
  exit 1
fi

ln -sfn "$release_dir" "$project_root/current"
docker compose exec -T app python scripts/verify_release.py
docker compose exec -T app python manage.py showmigrations economy
docker compose ps

# Refresh versioned deployment helpers only after the new application has
# passed its health and release checks. Local .env files and secrets are not
# part of this list and therefore remain untouched.
for helper in \
  backup.sh \
  bootstrap.sh \
  check-ownership.sh \
  configure-email.sh \
  configure-feedback.sh \
  install-diagnostics.sh \
  install-maintenance.sh \
  install.sh \
  install-release.sh \
  kinkudos-diagnose
do
  install -m 0755 "$release_dir/deploy/$helper" "$deploy_dir/$helper"
done
for support_file in \
  README.lt.md \
  README.md \
  compose.container-proxy.yml \
  compose.host-proxy.yml \
  compose.traefik.yml \
  kinkudos-lottery-reminders.service \
  kinkudos-lottery-reminders.timer \
  kinkudos-maintenance.service \
  kinkudos-maintenance.timer \
  restic.env.example
do
  install -m 0644 "$release_dir/deploy/$support_file" "$deploy_dir/$support_file"
done
install -m 0644 "$release_dir/deploy/.env.example" "$deploy_dir/.env.example"

# Keep only the successfully deployed source release. The running Docker image
# and application data are unaffected by removing older source directories.
for previous_release in "$releases_dir"/*; do
  if [ ! -d "$previous_release" ] || [ "$previous_release" = "$release_dir" ]; then
    continue
  fi
  rm -rf -- "$previous_release"
done

echo "KinKudos $version deployed successfully."
