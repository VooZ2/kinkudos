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
allowed_networks=${KINKUDOS_ALLOWED_NETWORKS:-192.168.0.0/16,10.0.0.0/8,172.16.0.0/12}
if [ -t 0 ]; then
  if [ "$install_language" = "lt" ]; then
    printf 'KinKudos domeno vardas [%s]: ' "$install_hostname"
    read -r selected_hostname
    printf 'Leidžiami privatūs tinklai [%s]: ' "$allowed_networks"
    read -r selected_networks
  else
    printf 'KinKudos hostname [%s]: ' "$install_hostname"
    read -r selected_hostname
    printf 'Allowed private networks [%s]: ' "$allowed_networks"
    read -r selected_networks
  fi
  install_hostname=${selected_hostname:-$install_hostname}
  allowed_networks=${selected_networks:-$allowed_networks}
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
    echo "KINKUDOS_ALLOWED_NETWORKS=$allowed_networks"
    echo "KINKUDOS_UID=$(id -u)"
    echo "KINKUDOS_GID=$(id -g)"
    echo "KINKUDOS_DEFAULT_LANGUAGE=$install_language"
  } > "$deploy_dir/.env"
elif ! grep -q '^KINKUDOS_DEFAULT_LANGUAGE=' "$deploy_dir/.env"; then
  printf 'KINKUDOS_DEFAULT_LANGUAGE=%s\n' "$install_language" >> "$deploy_dir/.env"
fi

mkdir -p \
  "$secrets_dir/backup" \
  "$secrets_dir/smtp" \
  "$project_root/data" \
  "$project_root/backups" \
  "$project_root/backup-state"

if [ ! -s "$secrets_dir/django_secret_key" ]; then
  openssl rand -base64 64 | tr -d '\n' > "$secrets_dir/django_secret_key"
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
  "$secrets_dir/restic_password" \
  "$secrets_dir/backup_agent_token" \
  "$secrets_dir/smtp_password" \
  "$secrets_dir/vapid_private.pem" \
  "$secrets_dir/vapid_public.txt" \
  "$secrets_dir/backup/restic.env"

cd "$deploy_dir"
docker compose config >/dev/null
docker compose build --pull
docker compose up -d
docker compose ps

if [ -t 0 ]; then
  if [ "$install_language" = "lt" ]; then
    printf 'Ar dabar sukurti tėvų paskyrą ir vaikų PIN? [Y/n] '
  else
    printf 'Create the parent account and child PINs now? [Y/n] '
  fi
  read -r answer
  case "$answer" in
    n|N) ;;
    *) docker compose exec app python manage.py setup_family --language "$install_language" ;;
  esac
fi

if [ "$install_language" = "lt" ]; then
  echo "Programos konteineris paleistas."
  echo "Patikra: docker compose ps"
  echo "Žurnalai: docker compose logs --tail=100 app"
else
  echo "The application container is running."
  echo "Status: docker compose ps"
  echo "Logs: docker compose logs --tail=100 app"
fi
