---
title: Install KinKudos with Docker Compose
description: Deploy KinKudos with the official Compose services, persistent host directories, generated secrets, and your existing HTTPS reverse proxy.
---

# Docker Compose installation

This route is for experienced self-hosters who want to integrate KinKudos with an existing Linux, NAS, Docker, or reverse-proxy environment. The supported deployment uses the release-owned files in `deploy/`; do not copy an isolated Compose snippet without its secrets, scripts, and proxy overlay.

## Deployment layout

```text
kinkudos/
├── app/            # retained release source
├── deploy/         # Compose, environment, and management scripts
├── data/
│   ├── kinkudos.sqlite3  # SQLite database
│   └── media/            # private uploaded images
├── backups/        # local database backup copies
├── backup-state/   # backup health state
└── secrets/        # setup, Django, VAPID, SMTP, and backup secrets
```

The base Compose file starts `app` and `backup-agent`. It publishes no application port. Select one supported overlay:

- `host` publishes `127.0.0.1:8000` for host Caddy or Nginx;
- `traefik` adds the configured Traefik router and external network;
- `container` joins an existing Nginx Proxy Manager or equivalent network.

Never publish port `8000` to the internet. Terminate HTTPS at the proxy and forward the original host and protocol.

## Install

The safest manual route is to download a specific GitHub release archive and SHA256 file, verify it, copy its `deploy` directory, then run the versioned `bootstrap.sh`. Exact verified commands are maintained in the repository’s [deployment reference](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.md#manual-verified-installation).

The bootstrap asks only for language, hostname, and the already prepared proxy mode. It generates required secrets and `.env`, validates the Compose configuration, pulls the image pinned to the selected KinKudos release, and starts the services.

After it prints the HTTPS URL and private setup code, continue with [First-time web setup](first-time-setup.md).

## Persistent data and secrets

Back up the complete `data/` directory: it contains both `kinkudos.sqlite3` and private uploads under `data/media/`. If remote backups are enabled, separately protect `secrets/restic_password` and `secrets/backup/restic.env`; they contain the password and repository settings needed to access those backups. Do not commit `.env`, `secrets`, databases, backups, or uploads. Removing or recreating a container must not remove these host directories. See [Backups and restore](../backups.md) for the supported procedure.

For later operations use [Updating](updating.md), [Backups](../backups.md), [CLI reference](../administration/cli.md), and [Troubleshooting](../troubleshooting.md).
