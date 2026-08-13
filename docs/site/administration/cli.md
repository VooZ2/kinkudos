---
title: KinKudos CLI command reference
description: Use verified KinKudos Docker Compose commands for status, logs, checks, maintenance, backups, password recovery, and emergency access.
---

# CLI command reference

Run these commands only from the correct `deploy` directory. Create a backup before account recovery or other sensitive operations.

| Purpose | Command |
|---|---|
| Status | `docker compose ps` |
| Application logs | `docker compose logs --tail=100 app` |
| Backup logs | `docker compose logs --tail=100 backup-agent` |
| Django deployment check | `docker compose exec -T app python manage.py check --deploy` |
| Run maintenance | `docker compose exec -T app python manage.py run_maintenance` |
| Send due lottery reminders, assigned-task nudges, and saved-set auto-assign | `docker compose exec -T app python manage.py send_lottery_reminders` |
| Disable a lockout-causing network restriction | `docker compose exec -T app python manage.py disable_network_restrictions` |
| Request configured remote backup | `./backup.sh` |
| Recover a parent password | `docker compose exec app python manage.py reset_parent_password --username PARENT_USERNAME` |
| Emergency account | `docker compose exec app python manage.py createsuperuser` |

Use `-T` for non-interactive commands. Omit it for password or account commands that need an interactive terminal. Do not use Django `shell` for normal administration or edit ledger, family, or account records directly.

`send_lottery_reminders` is the same roughly 30-minute timer used for optional lottery reminders. It also sends a soft child nudge when an assigned-task batch is still pending about three hours after it was sent, and it runs due saved assignment sets once per matching local day.

The older `setup_family` command remains a compatibility/advanced tool, not the supported first-time path. New installations use `/setup/` in the browser.
