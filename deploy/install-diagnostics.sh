#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this installer as root." >&2
  exit 1
fi

diagnostics_user=${1:-}
case "$diagnostics_user" in
  ""|*[!A-Za-z0-9_-]*)
    echo "Usage: sudo ./install-diagnostics.sh SYSTEM_USER" >&2
    exit 2
    ;;
esac

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
install -o root -g root -m 0755 \
  "$script_dir/kinkudos-diagnose" \
  /usr/local/sbin/kinkudos-diagnose

rule="/etc/sudoers.d/kinkudos-diagnose"
temporary=$(mktemp)
trap 'rm -f -- "$temporary"' EXIT INT TERM
printf '%s ALL=(root) NOPASSWD: /usr/local/sbin/kinkudos-diagnose ""\n' \
  "$diagnostics_user" > "$temporary"
chmod 0440 "$temporary"
visudo -cf "$temporary"
install -o root -g root -m 0440 "$temporary" "$rule"
echo "Diagnostics access installed for $diagnostics_user."
