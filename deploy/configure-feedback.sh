#!/bin/sh
set -eu

ENV_FILE="${1:-.env}"

if [ ! -f "$ENV_FILE" ]; then
  echo "Environment file not found: $ENV_FILE" >&2
  exit 1
fi

printf "Feedback notification email: "
IFS= read -r feedback_email

case "$feedback_email" in
  *@*.*) ;;
  *)
    echo "Enter a valid email address." >&2
    exit 1
    ;;
esac

temporary_file="$(mktemp "${ENV_FILE}.tmp.XXXXXX")"
trap 'rm -f "$temporary_file"' EXIT HUP INT TERM

awk -v feedback_email="$feedback_email" '
  BEGIN { updated = 0 }
  /^KINKUDOS_FEEDBACK_EMAIL=/ {
    if (!updated) {
      print "KINKUDOS_FEEDBACK_EMAIL=" feedback_email
      updated = 1
    }
    next
  }
  { print }
  END {
    if (!updated) {
      print "KINKUDOS_FEEDBACK_EMAIL=" feedback_email
    }
  }
' "$ENV_FILE" > "$temporary_file"

if file_mode="$(stat -c '%a' "$ENV_FILE" 2>/dev/null)"; then
  file_owner="$(stat -c '%u:%g' "$ENV_FILE")"
else
  file_mode="$(stat -f '%Lp' "$ENV_FILE")"
  file_owner="$(stat -f '%u:%g' "$ENV_FILE")"
fi
chmod "$file_mode" "$temporary_file"
chown "$file_owner" "$temporary_file"
mv "$temporary_file" "$ENV_FILE"
trap - EXIT HUP INT TERM

echo "Feedback email configured."
