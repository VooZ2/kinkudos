#!/bin/sh
set -eu

repository=${KINKUDOS_REPOSITORY:-VooZ2/kinkudos}
install_root=${KINKUDOS_INSTALL_ROOT:-/opt/kinkudos}
version=${KINKUDOS_VERSION:-}

fail() {
  echo "KinKudos installer: $*" >&2
  exit 1
}

for command in curl tar sha256sum docker openssl python3; do
  command -v "$command" >/dev/null 2>&1 || fail "required command not found: $command"
done
docker info >/dev/null 2>&1 || fail "Docker is not running or this user cannot access it."
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

if [ -e "$install_root" ] && [ -n "$(find "$install_root" -mindepth 1 -print -quit 2>/dev/null)" ]; then
  fail "$install_root is not empty; use the upgrade guide for an existing installation."
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

if [ ! -d "$install_root" ]; then
  if mkdir -p "$install_root" 2>/dev/null; then
    :
  elif command -v sudo >/dev/null 2>&1; then
    sudo install -d -o "$(id -u)" -g "$(id -g)" "$install_root"
  else
    fail "cannot create $install_root; choose a writable KINKUDOS_INSTALL_ROOT."
  fi
fi
[ -w "$install_root" ] || fail "$install_root is not writable by the current user."

tar -xzf "$work_dir/$archive" -C "$work_dir"
release_dir="$work_dir/kinkudos-$version"
test -d "$release_dir/deploy" || fail "release archive does not contain deploy files."
mv "$release_dir" "$install_root/app"
cp -a "$install_root/app/deploy" "$install_root/deploy"

echo "Starting the guided KinKudos setup..."
cd "$install_root/deploy"
./bootstrap.sh
