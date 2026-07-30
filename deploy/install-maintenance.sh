#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this installer with sudo." >&2
  exit 1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MAINTENANCE_SERVICE_TMP=$(mktemp)
LOTTERY_SERVICE_TMP=$(mktemp)
trap 'rm -f "$MAINTENANCE_SERVICE_TMP" "$LOTTERY_SERVICE_TMP"' EXIT

sed "s|@@KINKUDOS_DEPLOY_DIR@@|$SCRIPT_DIR|g" \
  "$SCRIPT_DIR/kinkudos-maintenance.service" > "$MAINTENANCE_SERVICE_TMP"
sed "s|@@KINKUDOS_DEPLOY_DIR@@|$SCRIPT_DIR|g" \
  "$SCRIPT_DIR/kinkudos-lottery-reminders.service" > "$LOTTERY_SERVICE_TMP"

install -o root -g root -m 0644 "$MAINTENANCE_SERVICE_TMP" /etc/systemd/system/kinkudos-maintenance.service
install -o root -g root -m 0644 "$LOTTERY_SERVICE_TMP" /etc/systemd/system/kinkudos-lottery-reminders.service
install -o root -g root -m 0644 "$SCRIPT_DIR/kinkudos-maintenance.timer" /etc/systemd/system/
install -o root -g root -m 0644 "$SCRIPT_DIR/kinkudos-lottery-reminders.timer" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now kinkudos-maintenance.timer
systemctl enable --now kinkudos-lottery-reminders.timer
systemctl status kinkudos-maintenance.timer --no-pager
systemctl status kinkudos-lottery-reminders.timer --no-pager
