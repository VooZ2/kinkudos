#!/bin/sh
set -eu

deploy_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_root=$(CDPATH= cd -- "$deploy_dir/.." && pwd)
secrets_dir="$project_root/secrets"

install_language=${KINKUDOS_DEFAULT_LANGUAGE:-en}
if [ -t 0 ]; then
  printf 'Installation language / Diegimo kalba [en/lt] (%s): ' "$install_language"
  read -r selected_language
  install_language=${selected_language:-$install_language}
fi
case "$install_language" in
  en|lt) ;;
  *) echo "Language must be en or lt / Kalba turi būti en arba lt." >&2; exit 1 ;;
esac

install_hostname=${KINKUDOS_HOSTNAME:-kinkudos.example.com}
proxy_mode=${KINKUDOS_PROXY_MODE:-host}
proxy_network=${KINKUDOS_PROXY_NETWORK:-web}
if [ -t 0 ]; then
  if [ "$install_language" = "lt" ]; then
    printf 'KinKudos domeno vardas [%s]: ' "$install_hostname"
    read -r selected_hostname
    printf 'Proxy režimas: host, traefik arba container [%s]: ' "$proxy_mode"
    read -r selected_proxy_mode
  else
    printf 'KinKudos hostname [%s]: ' "$install_hostname"
    read -r selected_hostname
    printf 'Proxy mode: host, traefik, or container [%s]: ' "$proxy_mode"
    read -r selected_proxy_mode
  fi
  install_hostname=${selected_hostname:-$install_hostname}
  proxy_mode=${selected_proxy_mode:-$proxy_mode}
fi
case "$proxy_mode" in
  host|traefik|container) ;;
  *) echo "Proxy mode must be host, traefik, or container." >&2; exit 1 ;;
esac

runtime_uid=$(id -u)
runtime_gid=$(id -g)
if [ "$runtime_uid" -eq 0 ]; then
  if [ -n "${SUDO_UID:-}" ] && [ -n "${SUDO_GID:-}" ]; then
    runtime_uid=$SUDO_UID
    runtime_gid=$SUDO_GID
  else
    echo "Do not run bootstrap directly as root; use a deployment user." >&2
    exit 1
  fi
fi

if ! command -v docker >/dev/null 2>&1; then
  [ "$install_language" = "lt" ] && echo "Klaida: Docker nerastas." >&2 \
    || echo "Error: Docker was not found." >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  [ "$install_language" = "lt" ] && echo "Klaida: šis naudotojas neturi Docker prieigos." >&2 \
    || echo "Error: this user cannot access Docker." >&2
  exit 1
fi

umask 077
if [ ! -f "$deploy_dir/.env" ]; then
  {
    echo "KINKUDOS_HOSTNAME=$install_hostname"
    echo "KINKUDOS_PROXY_MODE=$proxy_mode"
    echo "KINKUDOS_PROXY_NETWORK=$proxy_network"
    echo "KINKUDOS_UID=$runtime_uid"
    echo "KINKUDOS_GID=$runtime_gid"
    echo "KINKUDOS_DEFAULT_LANGUAGE=$install_language"
  } > "$deploy_dir/.env"
else
  if ! grep -q '^KINKUDOS_DEFAULT_LANGUAGE=' "$deploy_dir/.env"; then
    printf 'KINKUDOS_DEFAULT_LANGUAGE=%s\n' "$install_language" >> "$deploy_dir/.env"
  fi
  if ! grep -q '^KINKUDOS_PROXY_MODE=' "$deploy_dir/.env"; then
    printf 'KINKUDOS_PROXY_MODE=%s\n' "$proxy_mode" >> "$deploy_dir/.env"
  fi
  if ! grep -q '^KINKUDOS_PROXY_NETWORK=' "$deploy_dir/.env"; then
    printf 'KINKUDOS_PROXY_NETWORK=%s\n' "$proxy_network" >> "$deploy_dir/.env"
  fi
fi
"$deploy_dir/ensure-trusted-proxies.sh" "$deploy_dir/.env" "$proxy_mode" "$proxy_network"

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

for runtime_dir in \
  "$project_root/data" \
  "$project_root/backups" \
  "$project_root/backup-state"
do
  if [ -z "$(find "$runtime_dir" -mindepth 1 -print -quit)" ]; then
    chown "$runtime_uid:$runtime_gid" "$runtime_dir"
  fi
done

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
    | tail -c 65 \
    | base64 -w 0 \
    | tr '+/' '-_' \
    | tr -d '=' > "$secrets_dir/vapid_public.txt"
  printf '\n' >> "$secrets_dir/vapid_public.txt"
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
  "$deploy_dir/.env" \
  "$secrets_dir/django_secret_key" \
  "$secrets_dir/setup_token" \
  "$secrets_dir/restic_password" \
  "$secrets_dir/backup_agent_token" \
  "$secrets_dir/smtp_password" \
  "$secrets_dir/vapid_private.pem" \
  "$secrets_dir/vapid_public.txt" \
  "$secrets_dir/backup/restic.env"

cd "$deploy_dir"
case "$proxy_mode" in
  host) cp "$deploy_dir/compose.host-proxy.yml" "$deploy_dir/compose.override.yml" ;;
  traefik) cp "$deploy_dir/compose.traefik.yml" "$deploy_dir/compose.override.yml" ;;
  container) cp "$deploy_dir/compose.container-proxy.yml" "$deploy_dir/compose.override.yml" ;;
esac
"$deploy_dir/check-ownership.sh"
docker compose config >/dev/null
docker compose pull
docker compose up -d
docker compose ps

if [ "$install_language" = "lt" ]; then
  echo "Programos konteineris paleistas."
  echo "Atverkite https://$install_hostname/setup/ ir naršyklėje įveskite šį setup kodą:"
  cat "$secrets_dir/setup_token"
  echo "Patikra: docker compose ps"
  echo "Žurnalai: docker compose logs --tail=100 app"
else
  echo "The application container is running."
  echo "Open https://$install_hostname/setup/ and enter this setup code in the browser:"
  cat "$secrets_dir/setup_token"
  echo "Status: docker compose ps"
  echo "Logs: docker compose logs --tail=100 app"
fi
