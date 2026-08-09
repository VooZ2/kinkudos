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

## Choose the proxy mode before running the installer

The `bootstrap.sh` prompt does not install or configure a reverse proxy. It
selects the Compose overlay that matches a proxy you have already prepared.
Choose the mode according to the infrastructure that is already running:

| Prompt choice | Choose this when | What must already exist |
|---|---|---|
| `host` | Caddy or Nginx runs directly on the VPS | A proxy site for your hostname, DNS pointing to the VPS, and public ports 80/443 available |
| `traefik` | Traefik runs as a Docker service | The external Traefik network, `web` by default, and a working certificate resolver |
| `container` | Nginx Proxy Manager or another proxy runs in Docker | The external proxy network, `proxy` by default, and a route to the `app` service on port `8000` |

The hostname prompt takes the hostname only, without `https://` or a trailing
slash. The proxy mode prompt accepts exactly `host`, `traefik`, or `container`.
These choices describe how traffic is connected; they are not shell commands.

For `host`, configure the proxy upstream before starting KinKudos. A minimal
Caddy site is:

```caddyfile
family.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

Replace `family.example.com` with the hostname you entered during setup. For
Nginx, proxy the site to `http://127.0.0.1:8000` and pass the `Host`,
`X-Forwarded-Proto`, and `X-Forwarded-For` headers. Validate and reload the
proxy before expecting the public HTTPS address to work. For example:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

For Nginx, use `sudo nginx -t` and `sudo systemctl reload nginx` instead.

For `traefik` or `container`, set `KINKUDOS_PROXY_NETWORK` to the exact existing
Docker network name if it is not the default. For example:

```bash
KINKUDOS_PROXY_NETWORK=traefik-public ./bootstrap.sh
```

Select `traefik` only when Traefik is attached to that network. Select
`container` only when the other proxy is attached to it and is configured to
route to the KinKudos `app` service on port `8000`.

## Manual Docker Compose setup

Download a specific GitHub release archive and SHA256 file, verify it, and use
the release's `deploy/compose.yml` together with the matching proxy overlay.
The official files are maintained in the [deployment directory](https://github.com/VooZ2/kinkudos/tree/main/deploy).

Before starting, prepare the hostname or domain, HTTPS, a correctly configured
reverse proxy, and the persistent `data/`, `backups/`, `backup-state/`, and
`secrets/` directories. The `host`, `traefik`, and `container` overlays in
`deploy/` are the supported proxy choices.

The Compose file expects these host secret files to exist; Docker Compose does
not generate them:

```text
secrets/django_secret_key
secrets/setup_token
secrets/vapid_private.pem
secrets/vapid_public.txt
secrets/smtp_password       # may be empty when SMTP is disabled
secrets/restic_password
secrets/backup_agent_token
```

The backup agent also mounts `secrets/backup/`. The bootstrap script creates
that directory and a placeholder `restic.env`; configure that file when remote
backups are enabled.

Do not run the raw Compose command on an empty deployment root. Docker will warn
about missing secret files and then fail with an error such as
`invalid mount config ... secrets/restic_password`. For a new generic server,
use the [Guided server installer](guided-installer.md). For a verified manual
release installation, run `./bootstrap.sh` from the deployment directory as the
non-root deployment user first; it creates these files, the persistent
directories, and the selected proxy overlay before starting the services.

Choose a predictable release by keeping the image tag in `compose.yml` pinned:

```yaml
image: vooz2/kinkudos:<version>
```

From the directory containing your configured `compose.yml` (or the copied
release Compose files), start the application with:

```bash
docker compose up -d --pull always
```

The command pulls the selected image, starts the app and backup agent, and
keeps persistent data in the host directories. Using `latest` is possible only
as a conscious choice to follow the newest stable image; a version tag is
recommended for predictable deployments.

Check the result before opening the site:

```bash
docker compose ps
```

Wait for `app` to become `healthy`. If it does not, inspect
`docker compose logs --tail=100 app` and do not repeat the fresh installer over
the existing deployment.

For a fresh prepared server where you prefer an interactive setup, use the
[Guided server installer](guided-installer.md) instead. After Compose starts,
open your HTTPS URL and continue with [First-time web setup](first-time-setup.md).

## Persistent data and secrets

Back up the complete `data/` directory: it contains both `kinkudos.sqlite3` and private uploads under `data/media/`. If remote backups are enabled, separately protect `secrets/restic_password` and `secrets/backup/restic.env`; they contain the password and repository settings needed to access those backups. Do not commit `.env`, `secrets`, databases, backups, or uploads. Removing or recreating a container must not remove these host directories. See [Backups and restore](../backups.md) for the supported procedure.

For later operations use [Updating](updating.md), [Backups](../backups.md), [CLI reference](../administration/cli.md), and [Troubleshooting](../troubleshooting.md).
