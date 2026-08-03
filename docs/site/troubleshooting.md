---
title: Troubleshoot KinKudos installation and server problems
description: Diagnose domain, HTTPS, first-time setup, sign-in, SMTP, update, container, storage, and persistent-data problems safely.
---

# Troubleshooting

Start with the symptom. Do not delete containers, volumes, `data`, or `secrets` as a first response.

## KinKudos does not open

**Likely causes:** DNS points elsewhere, ports 80/443 are blocked, the proxy is stopped, or `app` is unhealthy.

**Check:**

```bash
getent hosts family.example.com
cd /opt/kinkudos/deploy
docker compose ps
```

For Hostinger run `/opt/kinkudos/deploy/hostinger-healthcheck.sh /opt/kinkudos`. Correct DNS or firewall access, then retry. Do not expose `8000`.

## Domain or HTTPS is not ready

The Hostinger health check reports **deployed but HTTPS pending** when KinKudos and Caddy run but the certificate is not yet usable. Confirm the hostname resolves to this VPS, inbound TCP 80 and 443 are allowed, and no other service occupies those ports. Wait for DNS propagation and rerun the health check.

Never bypass certificate errors or continue normal family use over public HTTP.

## Installer does not start

The Hostinger installer requires root, Hostinger Ubuntu 24.04 Docker, running Docker, Compose 2.20 or newer, Docker 24 or newer, and common system tools. Use its exact error instead of installing random packages or disabling checks.

The generic guided installer has different prerequisites and expects a non-root deployment user plus an existing HTTPS proxy. Do not mix the two profiles in one installation root.

## Setup page does not appear

`/setup/` is available only when no Django user or child exists and the family has not completed setup. On an unfinished installation, normal application pages redirect there.

If it redirects to parent sign-in or dashboard, setup has already been completed or migrated as complete. Do not attempt to unlock it. Use [password recovery](administration/password-recovery.md) for an existing family.

## Setup code is rejected

Copy the current code printed by the installer without extra spaces. In a Hostinger profile it is also stored in `/opt/kinkudos/secrets/setup_token` until setup succeeds. Treat it as a secret; do not place it in screenshots or support requests.

Re-running the recognized Hostinger installer preserves the existing setup code. Do not replace secret files manually.

## Cannot sign in

Confirm that you are using the parent sign-in page and the exact username created during setup. Use email recovery when SMTP works or the [CLI recovery command](administration/password-recovery.md). A child PIN works only on a paired child device and is not a parent password.

## Email recovery does not work

KinKudos intentionally hides email recovery while SMTP is disabled. Check the parent administrator’s **Email settings**, provider credentials, security mode, sender address, spam folder, and application logs. Saving settings verifies the SMTP connection; there is no separate documented test-email action in this release.

## Container stopped after an update

Preserve updater output, then run:

```bash
cd /opt/kinkudos/deploy
docker compose ps
docker compose logs --tail=100 app
```

The updater may restore the previous application image after a failed health check, but does not provide a general database rollback. Do not overwrite the live DB with an older copy. See [Updating](installation/updating.md).

## Disk space is low

Inspect the filesystem and Docker usage without deleting anything:

```bash
df -h
docker system df
```

Identify the exact source first. Preserve `data`, `backups`, `secrets`, and Caddy certificate volumes. Do not run broad Docker prune or recursive deletion commands on an unfamiliar server.

## Data appears missing after a Compose change

Stop making changes. A new empty bind mount can make the application look fresh while the original files still exist elsewhere. Record the active Compose configuration and mounts, preserve both locations, and do not complete `/setup/` over a suspected missing-data installation. Restore only after identifying the original `data` directory and following a tested recovery plan.

## Asking for help

GitHub Issues are for reproducible KinKudos bugs and feature requests, not general VPS administration. Include the KinKudos version, expected and actual result, safe reproduction steps, and a redacted log excerpt. Never include passwords, setup or recovery codes, API keys, `.env`, databases, backups, private family information, photos, or unredacted logs.
