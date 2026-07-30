#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this installer with sudo." >&2
  exit 1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SERVICE_TMP=$(mktemp)
trap 'rm -f "$SERVICE_TMP"' EXIT

sed "s|@@KINKUDOS_DEPLOY_DIR@@|$SCRIPT_DIR|g" \
  "$SCRIPT_DIR/kinkudos-maintenance.service" > "$SERVICE_TMP"

install -o root -g root -m 0644 "$SERVICE_TMP" /etc/systemd/system/kinkudos-maintenance.service
install -o root -g root -m 0644 "$SCRIPT_DIR/kinkudos-maintenance.timer" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now kinkudos-maintenance.timer
systemctl status kinkudos-maintenance.timer --no-pager
