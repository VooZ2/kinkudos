#!/usr/bin/env bash
set -Eeuo pipefail

deploy_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
project_root="$(CDPATH= cd -- "${deploy_dir}/.." && pwd)"
env_file="${deploy_dir}/.env"
secret_file="${project_root}/secrets/smtp_password"

if [ ! -f "$env_file" ]; then
  echo "${env_file} was not found. Complete the initial installation first." >&2
  exit 1
fi

install_language="$(sed -n 's/^KINKUDOS_DEFAULT_LANGUAGE=//p' "$env_file" | tail -n 1)"
case "$install_language" in
  lt)
    prompt_host="SMTP serveris (pvz., smtp.example.com): "
    prompt_port="SMTP prievadas [587]: "
    prompt_security="Šifravimas – tls, ssl arba none [tls]: "
    prompt_user="SMTP naudotojo vardas: "
    prompt_sender_name="Siuntėjo pavadinimas [KinKudos]: "
    prompt_sender_address="Siuntėjo adresas (pvz., app@example.com): "
    prompt_feedback_address="Atsiliepimų gavėjo adresas [toks pats kaip siuntėjo]: "
    prompt_password="SMTP slaptažodis: "
    default_sender_name="KinKudos"
    error_newline="Reikšmėse negali būti naujos eilutės."
    error_port="SMTP prievadas turi būti skaičius."
    error_security="Šifravimas turi būti tls, ssl arba none."
    error_required="Užpildykite SMTP serverį, naudotoją, slaptažodį ir teisingą siuntėjo adresą."
    success_message="SMTP konfigūracija įrašyta. Slaptos reikšmės nebuvo parodytos."
    ;;
  *)
    prompt_host="SMTP host (for example smtp.example.com): "
    prompt_port="SMTP port [587]: "
    prompt_security="Encryption — tls, ssl, or none [tls]: "
    prompt_user="SMTP username: "
    prompt_sender_name="Sender name [KinKudos]: "
    prompt_sender_address="Sender address (for example app@example.com): "
    prompt_feedback_address="Feedback recipient address [same as sender]: "
    prompt_password="SMTP password: "
    default_sender_name="KinKudos"
    error_newline="Values must not contain newline characters."
    error_port="The SMTP port must be a number."
    error_security="Encryption must be tls, ssl, or none."
    error_required="Provide an SMTP host, username, password, and a valid sender address."
    success_message="SMTP configuration saved. Secret values were not displayed."
    ;;
esac

read -r -p "$prompt_host" smtp_host
read -r -p "$prompt_port" smtp_port
smtp_port="${smtp_port:-587}"
read -r -p "$prompt_security" smtp_security
smtp_security="${smtp_security:-tls}"
read -r -p "$prompt_user" smtp_user
read -r -p "$prompt_sender_name" sender_name
sender_name="${sender_name:-$default_sender_name}"
read -r -p "$prompt_sender_address" sender_address
read -r -p "$prompt_feedback_address" feedback_address
feedback_address="${feedback_address:-$sender_address}"
read -r -s -p "$prompt_password" smtp_password
printf '\n'

case "$smtp_host$smtp_port$smtp_security$smtp_user$sender_name$sender_address$feedback_address$smtp_password" in
  *$'\n'*|*$'\r'*) echo "$error_newline" >&2; exit 1 ;;
esac
case "$smtp_port" in
  ''|*[!0-9]*) echo "$error_port" >&2; exit 1 ;;
esac
case "$smtp_security" in
  tls) smtp_use_tls=true; smtp_use_ssl=false ;;
  ssl) smtp_use_tls=false; smtp_use_ssl=true ;;
  none) smtp_use_tls=false; smtp_use_ssl=false ;;
  *) echo "$error_security" >&2; exit 1 ;;
esac
if [ -z "$smtp_host" ] || [ -z "$smtp_user" ] || [[ "$sender_address" != *@* ]] || [[ "$feedback_address" != *@* ]] || [ -z "$smtp_password" ]; then
  echo "$error_required" >&2
  exit 1
fi

umask 077
temporary_env="$(mktemp "${deploy_dir}/.env.email.XXXXXX")"
cleanup() {
  rm -f -- "$temporary_env"
}
trap cleanup EXIT

grep -v -E '^KINKUDOS_(EMAIL_ENABLED|EMAIL_HOST|EMAIL_PORT|EMAIL_USE_TLS|EMAIL_USE_SSL|EMAIL_HOST_USER|DEFAULT_FROM_EMAIL|FEEDBACK_EMAIL)=' "$env_file" \
  > "$temporary_env"
printf 'KINKUDOS_EMAIL_ENABLED=true\n' >> "$temporary_env"
printf 'KINKUDOS_EMAIL_HOST=%s\n' "$smtp_host" >> "$temporary_env"
printf 'KINKUDOS_EMAIL_PORT=%s\n' "$smtp_port" >> "$temporary_env"
printf 'KINKUDOS_EMAIL_USE_TLS=%s\n' "$smtp_use_tls" >> "$temporary_env"
printf 'KINKUDOS_EMAIL_USE_SSL=%s\n' "$smtp_use_ssl" >> "$temporary_env"
printf 'KINKUDOS_EMAIL_HOST_USER=%s\n' "$smtp_user" >> "$temporary_env"
printf 'KINKUDOS_DEFAULT_FROM_EMAIL=%s <%s>\n' "$sender_name" "$sender_address" >> "$temporary_env"
printf 'KINKUDOS_FEEDBACK_EMAIL=%s\n' "$feedback_address" >> "$temporary_env"
mv "$temporary_env" "$env_file"

printf '%s\n' "$smtp_password" > "$secret_file"
unset smtp_password
chmod 0600 "$env_file" "$secret_file"

echo "$success_message"
