---
title: Install KinKudos with Docker Compose
description: Deploy KinKudos with the official Compose services, persistent host directories, generated secrets, and your existing HTTPS reverse proxy.
---

# Docker Compose installation

This route is for experienced self-hosters who want to integrate KinKudos with an existing Linux, NAS, Docker, or reverse-proxy environment. Use the versioned files in the repository's `deploy/` directory; do not copy an isolated Compose snippet without its secrets, scripts, and proxy overlay.

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

## Manual Docker Compose setup

Download a specific GitHub release archive and SHA256 file, verify it, and use
the release's `deploy/compose.yml` together with the matching proxy overlay.
The official files are maintained in the [deployment directory](https://github.com/VooZ2/kinkudos/tree/main/deploy).

Before starting, prepare the required environment variables and secret files,
persistent `data/`, `backups/`, and `secrets/` directories, a hostname or
domain, HTTPS, and a correctly configured reverse proxy. The `host`, `traefik`,
and `container` overlays in `deploy/` are the supported proxy choices.

Choose a predictable release by keeping the image tag in `compose.yml` pinned:

```yaml
image: vooz2/kinkudos:<version>
```

From the directory containing your configured `compose.yaml` (or the copied
release Compose files), start the application with:

```bash
docker compose up -d --pull always
```

The command pulls the selected image, starts the app and backup agent, and
keeps persistent data in the host directories. Using `latest` is possible only
as a conscious choice to follow the newest stable image; a version tag is
recommended for predictable deployments.

For a fresh prepared server where you prefer an interactive setup, use the
[Guided server installer](guided-installer.md) instead. After Compose starts,
open your HTTPS URL and continue with [First-time web setup](first-time-setup.md).

## Persistent data and secrets

Back up the complete `data/` directory: it contains both `kinkudos.sqlite3` and private uploads under `data/media/`. If remote backups are enabled, separately protect `secrets/restic_password` and `secrets/backup/restic.env`; they contain the password and repository settings needed to access those backups. Do not commit `.env`, `secrets`, databases, backups, or uploads. Removing or recreating a container must not remove these host directories. See [Backups and restore](../backups.md) for the supported procedure.

For later operations use [Updating](updating.md), [Backups](../backups.md), [CLI reference](../administration/cli.md), and [Troubleshooting](../troubleshooting.md).
