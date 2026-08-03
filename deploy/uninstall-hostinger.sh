#!/bin/sh
set -eu

profile=hostinger-caddy-v1
project_root=${1:-/opt/kinkudos}
profile_file="$project_root/install-profile"

[ "$(id -u)" -eq 0 ] || { echo "Run this command as root." >&2; exit 1; }
[ -f "$profile_file" ] && [ "$(cat "$profile_file")" = "$profile" ] \
  || { echo "Refusing to stop an unrecognized installation profile." >&2; exit 1; }
[ -f "$project_root/deploy/compose.yml" ] \
  || { echo "KinKudos Compose configuration was not found." >&2; exit 1; }

cd "$project_root/deploy"
docker compose down
echo "KinKudos containers were removed."
echo "Application data, secrets, backups, installation files, and Caddy certificate volumes were retained."
echo "Run install-hostinger.sh again to resume this installation."
