#!/bin/sh
set -eu

repository=${KINKUDOS_REPOSITORY:-VooZ2/kinkudos}
install_root=${KINKUDOS_INSTALL_ROOT:-/opt/kinkudos}
version=${KINKUDOS_VERSION:-}
profile=hostinger-caddy-v1

fail() {
  echo "KinKudos Hostinger installer: $*" >&2
  exit 1
}

[ "$(id -u)" -eq 0 ] || fail "run this installer as root in Hostinger Browser Terminal."

for command in curl tar sha256sum docker python3; do
  command -v "$command" >/dev/null 2>&1 || fail "required command not found: $command"
done
docker info >/dev/null 2>&1 || fail "Docker is not running. Use the Hostinger Ubuntu 24.04 Docker template."
docker compose version >/dev/null 2>&1 || fail "Docker Compose plugin was not found."

if [ -z "$version" ]; then
  latest_url=$(curl -fsSL -o /dev/null -w '%{url_effective}' \
    "https://github.com/$repository/releases/latest")
  version=${latest_url##*/}
  version=${version#v}
fi
case "$version" in
  *[!0-9.]*|.*|*..*|*.) fail "invalid release version: $version" ;;
esac

profile_file="$install_root/install-profile"
release_file="$install_root/installed-release"
if [ -e "$install_root" ] && [ -n "$(find "$install_root" -mindepth 1 -print -quit 2>/dev/null)" ]; then
  [ -f "$profile_file" ] || fail "$install_root is not empty and has no KinKudos installation profile."
  [ "$(cat "$profile_file")" = "$profile" ] || fail "unsupported installation profile in $profile_file."
  if [ -s "$release_file" ] && [ "$(cat "$release_file")" != "$version" ]; then
    fail "KinKudos $(cat "$release_file") is already installed; use the supported update procedure."
  fi
fi

work_dir=$(mktemp -d)
cleanup() {
  rm -rf -- "$work_dir"
}
trap cleanup EXIT INT TERM

archive="kinkudos-$version.tar.gz"
checksum="$archive.sha256"
release_url="https://github.com/$repository/releases/download/v$version"

echo "Downloading KinKudos $version..."
curl -fL --retry 3 -o "$work_dir/$archive" "$release_url/$archive"
curl -fL --retry 3 -o "$work_dir/$checksum" "$release_url/$checksum"
(
  cd "$work_dir"
  sha256sum -c "$checksum"
)

python3 - "$work_dir/$archive" <<'PY'
import sys
import tarfile
from pathlib import PurePosixPath

with tarfile.open(sys.argv[1], "r:gz") as archive:
    for member in archive.getmembers():
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts or member.issym() or member.islnk():
            raise SystemExit(f"Unsafe archive member: {member.name}")
PY

tar -xzf "$work_dir/$archive" -C "$work_dir"
release_dir="$work_dir/kinkudos-$version"
test -x "$release_dir/deploy/hostinger-bootstrap.sh" \
  || fail "release archive does not contain the Hostinger bootstrap."

mkdir -p "$install_root"
umask 077
if [ ! -f "$profile_file" ]; then
  printf '%s\n' "$profile" > "$profile_file"
fi

if [ ! -d "$install_root/app" ]; then
  cp -a "$release_dir" "$install_root/app"
else
  installed_app_version=$(sed -n 's/^version = "\([^"]*\)"$/\1/p' \
    "$install_root/app/pyproject.toml" 2>/dev/null | head -n 1)
  [ "$installed_app_version" = "$version" ] \
    || fail "the existing app directory does not match KinKudos $version."
fi
mkdir -p "$install_root/deploy"
cp -a "$release_dir/deploy/." "$install_root/deploy/"
printf '%s\n' "$version" > "$release_file"
chmod 0600 "$profile_file" "$release_file"

exec "$install_root/deploy/hostinger-bootstrap.sh" "$install_root"
