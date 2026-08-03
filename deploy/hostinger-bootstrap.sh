#!/bin/sh
set -eu

profile=hostinger-caddy-v1
project_root=${1:-/opt/kinkudos}
deploy_dir="$project_root/deploy"
secrets_dir="$project_root/secrets"
profile_file="$project_root/install-profile"

fail() {
  echo "KinKudos Hostinger bootstrap: $*" >&2
  exit 1
}

read_env() {
  sed -n "s/^$1=//p" "$deploy_dir/.env" 2>/dev/null | tail -n 1
}

version_at_least() {
  [ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | head -n 1)" = "$2" ]
}

[ "$(id -u)" -eq 0 ] || fail "run this bootstrap as root."
[ -r /etc/os-release ] || fail "cannot identify the operating system."
. /etc/os-release
[ "${ID:-}" = ubuntu ] && [ "${VERSION_ID:-}" = "24.04" ] \
  || fail "this profile supports the Hostinger Ubuntu 24.04 Docker template only."
[ -f "$profile_file" ] && [ "$(cat "$profile_file")" = "$profile" ] \
  || fail "the Hostinger installation profile marker is missing or invalid."

for command in curl docker openssl python3 sort ss; do
  command -v "$command" >/dev/null 2>&1 || fail "required command not found: $command"
done
docker info >/dev/null 2>&1 || fail "Docker is not running."
docker compose version >/dev/null 2>&1 || fail "Docker Compose plugin was not found."
docker_version=$(docker version --format '{{.Server.Version}}' | sed 's/[^0-9.].*$//')
compose_version=$(docker compose version --short | sed 's/[^0-9.].*$//')
version_at_least "$docker_version" 24.0.0 || fail "Docker 24.0.0 or newer is required."
version_at_least "$compose_version" 2.20.0 || fail "Docker Compose 2.20.0 or newer is required."

install_language=${KINKUDOS_DEFAULT_LANGUAGE:-}
install_hostname=${KINKUDOS_HOSTNAME:-}
if [ -f "$deploy_dir/.env" ]; then
  saved_profile=$(read_env KINKUDOS_INSTALL_PROFILE)
  [ "$saved_profile" = "$profile" ] || fail "deploy/.env belongs to another installation profile."
  install_language=$(read_env KINKUDOS_DEFAULT_LANGUAGE)
  install_hostname=$(read_env KINKUDOS_HOSTNAME)
else
  install_language=${install_language:-en}
  if [ -t 0 ]; then
    printf 'Installation language / Diegimo kalba [en/lt] (%s): ' "$install_language"
    read -r selected_language
    install_language=${selected_language:-$install_language}
    printf 'KinKudos hostname / domeno vardas: '
    read -r install_hostname
  fi
fi
case "$install_language" in
  en|lt) ;;
  *) fail "language must be en or lt." ;;
esac
[ -n "$install_hostname" ] || fail "set KINKUDOS_HOSTNAME or enter a hostname interactively."
python3 - "$install_hostname" <<'PY'
import re
import sys

hostname = sys.argv[1]
if len(hostname) > 253 or not re.fullmatch(
    r"(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}",
    hostname,
):
    raise SystemExit("Invalid public hostname. Use a lowercase fully qualified domain name.")
PY

cd "$deploy_dir"
existing_caddy=$(docker compose ps -q caddy 2>/dev/null || true)
if [ -z "$existing_caddy" ]; then
  for port in 80 443; do
    if ss -ltn "sport = :$port" | sed 1d | grep -q .; then
      fail "TCP port $port is already in use. Stop the conflicting web server or proxy first."
    fi
  done
fi

umask 077
if [ ! -f "$deploy_dir/.env" ]; then
  {
    echo "KINKUDOS_INSTALL_PROFILE=$profile"
    echo "KINKUDOS_HOSTNAME=$install_hostname"
    echo "KINKUDOS_PROXY_MODE=hostinger"
    echo "KINKUDOS_UID=1000"
    echo "KINKUDOS_GID=1000"
    echo "KINKUDOS_DEFAULT_LANGUAGE=$install_language"
  } > "$deploy_dir/.env"
fi

mkdir -p \
  "$secrets_dir/backup" \
  "$secrets_dir/smtp" \
  "$project_root/data" \
  "$project_root/backups" \
  "$project_root/backup-state"
chown 1000:1000 \
  "$project_root/data" \
  "$project_root/backups" \
  "$project_root/backup-state" \
  "$secrets_dir/backup" \
  "$secrets_dir/smtp"

if [ ! -s "$secrets_dir/django_secret_key" ]; then
  openssl rand -base64 64 | tr -d '\n' > "$secrets_dir/django_secret_key"
fi
if [ ! -s "$secrets_dir/setup_token" ]; then
  openssl rand -base64 36 | tr -d '\n' > "$secrets_dir/setup_token"
fi
if [ ! -s "$secrets_dir/restic_password" ]; then
  openssl rand -base64 48 | tr -d '\n' > "$secrets_dir/restic_password"
fi
if [ ! -s "$secrets_dir/backup_agent_token" ]; then
  openssl rand -base64 48 | tr -d '\n' > "$secrets_dir/backup_agent_token"
fi
if [ ! -f "$secrets_dir/smtp_password" ]; then
  : > "$secrets_dir/smtp_password"
fi
if [ ! -s "$secrets_dir/vapid_private.pem" ]; then
  openssl ecparam -name prime256v1 -genkey -noout -out "$secrets_dir/vapid_private.pem"
fi
if [ ! -s "$secrets_dir/vapid_public.txt" ]; then
  openssl ec -in "$secrets_dir/vapid_private.pem" -pubout -outform DER 2>/dev/null \
    | tail -c 65 | base64 -w 0 | tr '+/' '-_' | tr -d '=' > "$secrets_dir/vapid_public.txt"
  printf '\n' >> "$secrets_dir/vapid_public.txt"
fi
if [ ! -f "$secrets_dir/backup/restic.env" ]; then
  {
    echo "# Choose any repository type supported by restic."
    echo "RESTIC_REPOSITORY=REPLACE_WITH_REPOSITORY"
  } > "$secrets_dir/backup/restic.env"
fi
chmod 0600 \
  "$deploy_dir/.env" \
  "$secrets_dir/django_secret_key" \
  "$secrets_dir/setup_token" \
  "$secrets_dir/restic_password" \
  "$secrets_dir/backup_agent_token" \
  "$secrets_dir/smtp_password" \
  "$secrets_dir/vapid_private.pem" \
  "$secrets_dir/vapid_public.txt" \
  "$secrets_dir/backup/restic.env"
chown 1000:1000 \
  "$secrets_dir/backup_agent_token" \
  "$secrets_dir/setup_token" \
  "$secrets_dir/restic_password" \
  "$secrets_dir/backup/restic.env"

if [ ! -f "$deploy_dir/Caddyfile" ]; then
  cp "$deploy_dir/Caddyfile.hostinger" "$deploy_dir/Caddyfile"
fi
grep -Fq '{$KINKUDOS_HOSTNAME}' "$deploy_dir/Caddyfile" \
  || fail "the existing Caddyfile is not the supported Hostinger configuration."
if [ ! -f "$deploy_dir/compose.override.yml" ]; then
  cp "$deploy_dir/compose.hostinger.yml" "$deploy_dir/compose.override.yml"
fi
grep -Fq 'caddy:2.11.4-alpine' "$deploy_dir/compose.override.yml" \
  || fail "compose.override.yml is not the supported Hostinger Caddy profile."

"$deploy_dir/check-ownership.sh" "$project_root"
docker compose config --quiet
docker compose pull
docker compose up -d

set +e
"$deploy_dir/hostinger-healthcheck.sh" "$project_root"
health_status=$?
set -e
case "$health_status" in
  0|2) ;;
  *) exit "$health_status" ;;
esac

echo
echo "Setup URL: https://$install_hostname/setup/"
echo "Setup code: $(cat "$secrets_dir/setup_token")"
echo "Keep the setup code private. It remains valid until setup finishes successfully."
echo "Hostinger firewall: allow inbound TCP ports 80 and 443."
exit 0
