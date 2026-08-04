#!/bin/sh
set -eu

runtime_secrets_dir=${KINKUDOS_RUNTIME_SECRETS_DIR:-}
if [ -n "$runtime_secrets_dir" ]; then
  mkdir -p "$runtime_secrets_dir"
  chmod 0700 "$runtime_secrets_dir"

  secret_key_file="$runtime_secrets_dir/django_secret_key"
  if [ ! -s "$secret_key_file" ]; then
    umask 077
    python -c 'import secrets; print(secrets.token_urlsafe(64))' > "$secret_key_file"
  fi

  vapid_private_file="$runtime_secrets_dir/vapid_private.pem"
  vapid_public_file="$runtime_secrets_dir/vapid_public.txt"
  if [ -e "$vapid_private_file" ] || [ -e "$vapid_public_file" ]; then
    if [ ! -s "$vapid_private_file" ] || [ ! -s "$vapid_public_file" ]; then
      echo "KinKudos runtime VAPID keys are incomplete." >&2
      exit 1
    fi
  else
    umask 077
    python -c 'from economy.vapid import generate_vapid_keys; import os; generate_vapid_keys(os.environ["KINKUDOS_RUNTIME_SECRETS_DIR"])'
  fi
fi

python manage.py migrate --noinput

exec "$@"
