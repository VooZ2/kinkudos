# Deployment

This directory lives next to the application source directory on the server.
The suggested layout is:

```text
kinkudos/
├── app/                 # optional retained release source
├── deploy/
├── data/
├── backups/
├── backup-state/
├── uploads/
└── secrets/
```

Lithuanian documentation: [README.lt.md](README.lt.md)

## Secrets

The `secrets` directory contains:

- `django_secret_key` — at least 64 random characters;
- `vapid_private.pem`;
- `vapid_public.txt`;
- `restic_password`;
- `backup_agent_token`;
- `backup/restic.env` (created as a placeholder by the bootstrap script and
  configured when external `restic` backups are used);
- `smtp_password` (the file is required by Compose but may be empty when email
  is disabled).

Secret files must be owned by the deployment administrator and have `0600`
permissions. Never commit `.env` or the `secrets` directory.

The base Compose file does not create these host files. Do not run a raw
`docker compose up` from an empty deployment root: Docker will report missing
secret files and fail when it tries to bind-mount one of them. On a fresh
generic installation, run `./bootstrap.sh` from this directory as the non-root
deployment user. It creates the required files and persistent directories,
selects the proxy overlay, and starts the services. Use the raw Compose command
only after the deployment has been initialized.

## Installation

Prerequisites:

- a fresh 64-bit ARM or x86 Linux host and an administrator account with
  `sudo` access;
- an HTTPS reverse proxy: Nginx, Caddy, Nginx Proxy Manager, Traefik, or an
  equivalent product;
- a hostname routed to the host;
- access to the chosen release archive and its SHA256 checksum. When using
  GitHub CLI with a private repository, authenticate an account that can read
  that repository;
- access to the public `vooz2/kinkudos` Docker Hub image.

### Hostinger Ubuntu 24.04 Docker profile

For a new Hostinger VPS created from the **Ubuntu 24.04 with Docker** template,
point the final hostname to the VPS and use Docker Manager's **Compose
manually** flow with `deploy/hostinger/compose.yaml`. The template-provided
Traefik application handles HTTPS; do not add Caddy or expose port `8000`.
Set `KINKUDOS_HOSTNAME` and a private `KINKUDOS_SETUP_TOKEN` in Docker Manager
before deployment. Follow the complete
[Hostinger user guide](https://docs.kinkudos.app/installation/hostinger/).

### Quick installation on a prepared server

Use this option on a fresh server that already has Docker Engine, the Docker
Compose plugin, a hostname routed to the server, and a supported HTTPS reverse
proxy:

```bash
curl -fsSL https://kinkudos.app/install.sh -o /tmp/kinkudos-install.sh && sh /tmp/kinkudos-install.sh
```

The installer discovers the latest release, downloads its archive and checksum,
verifies SHA256, creates `/opt/kinkudos`, and starts the guided setup. Run it as
the normal deployment user, not as root. Set `KINKUDOS_VERSION` to install a
specific release or `KINKUDOS_INSTALL_ROOT` to choose another root directory.

This command is only for a fresh installation. If KinKudos is already
installed, follow [Updating an existing installation](#updating-an-existing-installation).

### Preparing a fresh Ubuntu server

The commands below prepare a current supported Ubuntu Server installation.
For another Linux distribution, use the official
[Docker Engine installation instructions](https://docs.docker.com/engine/install/)
and install the Docker Compose plugin (the legacy standalone `docker-compose`
binary is not used). Keep SSH access open and allow inbound HTTP/HTTPS traffic
on ports 80 and 443. Do not expose port 8000 publicly.

Install Docker Engine and the Compose plugin from Docker's official Apt
repository:

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

Membership in the `docker` group grants root-equivalent host access. Log out
and sign in again before continuing, then verify both components:

```bash
docker run --rm hello-world
docker compose version
```

Install GitHub CLI from its official Apt repository:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null
sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
  | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
sudo apt update
sudo apt install -y gh
```

Public releases and the public Docker Hub image do not require registry login.
For a private GitHub repository, authenticate GitHub CLI with `gh auth login`.

For the simplest host-proxy setup, install Caddy from its official repository.
You may instead install one of the other supported proxies and select the
matching mode in `bootstrap.sh`.

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https gnupg
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
  | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
  | sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg \
  /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

Confirm that the chosen hostname resolves to this server before expecting the
proxy to obtain a TLS certificate.

### Manual verified installation

For a manual installation from a new empty deployment root, set
`KINKUDOS_VERSION` to the release you want, then download and verify it, keep
its source as `app`, copy out the deployment directory, and start the same
guided setup:

```bash
sudo install -d -o "$USER" -g "$(id -gn)" /opt/kinkudos
cd /opt/kinkudos
version=${KINKUDOS_VERSION:?Set KINKUDOS_VERSION before running this block}
repository=VooZ2/kinkudos
gh release download "v$version" --repo "$repository" \
  --pattern "kinkudos-$version.tar.gz*"
sha256sum -c "kinkudos-$version.tar.gz.sha256"
tar -xzf "kinkudos-$version.tar.gz"
mv "kinkudos-$version" app
cp -a app/deploy ./deploy
cd deploy
./bootstrap.sh
```

When using the host Caddy mode, replace the example hostname in
`/etc/caddy/Caddyfile` with the hostname entered in the installer:

```caddyfile
family.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

Then validate and reload Caddy:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Open `https://family.example.com`, using your real hostname. The installer
shows container status at the end; `docker compose ps` and
`docker compose logs --tail=100 app` provide the same checks later.

The installer asks for English or Lithuanian, hostname, and reverse-proxy mode.
It generates missing Django, VAPID, backup-agent, restic, and browser-setup
secrets, creates `.env`, checks host-directory ownership, pulls the published
application image, and starts the containers. It then prints the application
URL and a setup code. Open `/setup/` in a browser and create the first parent,
family name, language, and timezone there. Existing secrets are not overwritten.

For an unattended English installation, set:

```bash
KINKUDOS_DEFAULT_LANGUAGE=en ./bootstrap.sh
```

Use `lt` instead of `en` for Lithuanian. Users can still switch language in the
web interface; their choice is saved on that device.

The setup code is needed only while no parent account exists. Keep it private;
after browser setup the server permanently disables the setup route.

## Updating an existing installation

Run these commands from the deployment root (the directory containing
`app`, `deploy`, `data`, and `secrets`). Set `KINKUDOS_VERSION` to the release
you want to install before running this block:

```bash
version=${KINKUDOS_VERSION:?Set KINKUDOS_VERSION before running this block}
repository=VooZ2/kinkudos
gh release download "v$version" --repo "$repository" \
  --pattern "kinkudos-$version.tar.gz*"
sha256sum -c "kinkudos-$version.tar.gz.sha256"
install_script="$(mktemp)"
compose_file="$(mktemp)"
tar -xOf "kinkudos-$version.tar.gz" \
  "kinkudos-$version/deploy/install-release.sh" > "$install_script"
tar -xOf "kinkudos-$version.tar.gz" \
  "kinkudos-$version/deploy/compose.yml" > "$compose_file"
sudo install -m 0644 "$compose_file" deploy/compose.yml
sudo sh "$install_script" \
  "$PWD/kinkudos-$version.tar.gz" \
  "$PWD/kinkudos-$version.tar.gz.sha256" \
  "$version" \
  "$PWD"
rm -f "$install_script" "$compose_file"
```

### RC build — only when VPS / installer acceptance is needed

A release candidate is not required for every release or every commit. For real
VPS, installer, or deployment acceptance, open GitHub Actions → **Build release
candidate** → **Run workflow** and set `source_ref` to the relevant
`release/<version>` branch or a full commit SHA contained by a release branch.
A normal push to `release/<version>` does not create an RC. The RC is QA-only;
stable publication remains a separate process, and a release that does not need
VPS/deployment acceptance may proceed without an RC.

### Release-candidate acceptance testing (maintainers only)

`KINKUDOS_IMAGE_REPOSITORY` and `KINKUDOS_IMAGE_TAG` are explicit RC-only
overrides. When testing a candidate image, pass both through `sudo env` to the
release updater and pass them again to every later Compose command that resolves
or recreates images, for example:

```bash
candidate_tag=26.8.2-rc.<short-sha>
sudo env KINKUDOS_IMAGE_REPOSITORY=vooz2/kinkudos-rc \
  KINKUDOS_IMAGE_TAG="$candidate_tag" docker compose pull
sudo env KINKUDOS_IMAGE_REPOSITORY=vooz2/kinkudos-rc \
  KINKUDOS_IMAGE_TAG="$candidate_tag" docker compose up -d --force-recreate
```

The overrides are intentionally not persisted in the production `.env`. This is
not the normal stable-user update workflow. For a stable `26.8.2` update, use
the procedure above without either override; the Compose defaults are the
production `vooz2/kinkudos` package and `26.8.2`.

The updater validates the checksum and release metadata, pulls and smoke-tests
the published image, checks host-directory ownership, backs up the live
database, switches the app only after those checks pass, verifies container
health, and refreshes versioned `deploy` management scripts. The application
has outbound access for DNS, HTTPS, SMTP, and Web Push through a dedicated
non-internal Compose network, while the backup-agent control network remains
internal and its backup storage network is separate. The local
`deploy/.env`, runtime data, uploads, backups, and secrets remain untouched and
are never included in the release archive.

If the new container fails its health check after startup, the updater stops
with an explicit compatibility warning. It does not silently restore the old
image because the new image may already have applied database migrations; an
operator must resolve the compatibility issue or perform a separately verified
restore before choosing an older image.

## Reverse proxy and client IPs

The base Compose file does not publish the application port and is independent
of a particular reverse proxy. `bootstrap.sh` creates one local
`compose.override.yml`:

- `compose.host-proxy.yml` publishes `127.0.0.1:8000` for host-installed Nginx
  or Caddy;
- `compose.container-proxy.yml` connects the app to a configurable external
  Docker network for Nginx Proxy Manager or another container proxy;
- `compose.traefik.yml` adds the KinKudos Traefik router and the selected
  external Docker network.

For host Nginx, proxy to `http://127.0.0.1:8000` and pass the original
`Host`, `X-Forwarded-Proto`, and `X-Forwarded-For` headers:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

A minimal Caddy site is:

```caddyfile
family.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

For Nginx Proxy Manager, select the Docker service `app`, port `8000`, enable
WebSocket support, and use the same external network configured by
`KINKUDOS_PROXY_NETWORK`.

KinKudos trusts forwarded client-IP headers only when the direct peer belongs
to `KINKUDOS_TRUSTED_PROXIES`. The application default is loopback only.
`bootstrap.sh` and `install-release.sh` write this value automatically:

- host Nginx/Caddy → `127.0.0.0/8,::1/128`;
- Traefik or another container proxy → the selected Docker network subnet from
  `docker network inspect` (or one interactive CIDR prompt if the network is
  missing).

An existing non-empty `.env` value is never overwritten. Hostinger Docker
Manager installs keep the Compose fallback
`10.0.0.0/8,172.16.0.0/12` and do not use this helper. Never set the value to
the entire internet. The optional parent setting
Settings → Network access can then restrict child pages or the entire
application to explicit IP/CIDR networks. It is disabled by default and is an
additional layer, not a replacement for HTTPS, device pairing, or strong
parent passwords. If a rule locks out every parent, run:

```bash
docker compose exec -T app python manage.py disable_network_restrictions
```

The Django administration route is disabled by default. Normal family
administration remains in the parent interface.

Before installation or update, `check-ownership.sh` verifies that bind-mounted
directories are writable by the configured `APP_UID` and `APP_GID`. If it
reports a mismatch, review the exact path and apply the shown `chown` command;
do not recursively change ownership of the deployment root.

## Backups

The isolated `backup-agent` creates a consistent SQLite backup, includes
uploaded media, and sends encrypted snapshots to Backblaze B2 or another
S3-compatible repository. Configure it as the first parent under
Settings → Backups. During an upgrade, an existing valid
`secrets/restic.env` is migrated to `secrets/backup/restic.env`;
`secrets/restic_password` is preserved.

This KinKudos-managed remote backup is separate from any whole-server or
hosting-provider backup. The web interface reports only snapshots created by
the KinKudos backup agent. For Backblaze B2, use a dedicated bucket and an
application key restricted to that bucket; use a separate bucket and test data
for release verification.

If saving the configuration reports that the storage server cannot be
resolved, the backup container could not translate the S3 endpoint hostname to
an IP address. This happens before credentials are checked. Verify that the
endpoint contains only the provider hostname (for example,
`s3.eu-central-003.backblazeb2.com`) and then inspect DNS and agent logs:

Run these commands from the deployment root that contains the `deploy`
directory:

```bash
docker compose -f deploy/compose.yml exec -T backup-agent python -c \
  "import socket; print(socket.getaddrinfo('s3.eu-central-003.backblazeb2.com', 443))"
docker compose -f deploy/compose.yml logs --tail=100 backup-agent
```

Replace the example hostname with the endpoint entered in KinKudos. A
`Name or service not known` result usually means a misspelled/nonexistent
endpoint; a timeout or `server misbehaving` result points to Docker daemon or
host DNS/network configuration.

To request the same verified backup from the server:

```bash
./backup.sh
```

Backups run automatically once per day after 03:00 server time. Set
`KINKUDOS_BACKUP_HOUR` in `deploy/.env` to choose another hour. Local database
copies and remote daily snapshots are retained for 31 days. A successful run
includes `restic check`. A failed scheduled attempt is not recorded as that
day's success; the agent retries later the same day with bounded backoff, and a
successful scheduled run is not repeated that day.

Keep an offline copy of `secrets/restic_password`. Restore is intentionally a
server-administrator procedure and must be tested in a separate directory.

## Password reset email

The application supports standard SMTP and is not tied to a particular email
provider. Create a dedicated SMTP credential for KinKudos, then run:

```bash
./configure-email.sh
```

The script asks for the SMTP host, port, TLS/SSL mode, username, sender name,
sender address, and the address that should receive saved feedback
notifications. The password is written to `../secrets/smtp_password` with
`0600` permissions and is never echoed or placed in shell history.

Email is disabled by default until SMTP is configured. A parent administrator
can later verify and change the same settings in Settings → Email after
confirming their current parent password. UI-managed values, including the
password, are stored in `../secrets/smtp/settings.json` with `0600`
permissions and are never stored in the application database.

Signed-in parents and children can submit a private family problem or
suggestion from the floating bug button. KinKudos saves the report before
attempting email delivery. Parents can review and update report statuses in
Settings even if SMTP is unavailable. Software defects belong in the linked
GitHub issue tracker; reports sent there must not contain names, screenshots,
or other family data. Optional in-app screenshots are private WebP files; only
screenshots from resolved reports are removed after the retention period
selected in Settings.

## Scheduled maintenance, lottery reminders, and assignment presets

KinKudos keeps task photos and resolved-feedback screenshots for the periods
selected in the parent settings. Every 30 minutes the same reminder command (`run_scheduled_reminders`, with
legacy alias `send_lottery_reminders`) also:

- checks whether a due weekly lottery reminder should be sent;
- sends soft assigned-task nudges when a batch is still pending about three
  hours after assignment (still on that local calendar day);
- runs due saved assignment presets (family timezone, at/after each set’s
  send time, once per matching day when work is available).

Do not disable this timer as a “lottery-only” job — assignment nudges and
saved-set auto-assign use it too.

On a systemd-based Docker host, enable both timers after installation or an
upgrade:

```bash
cd /path/to/kinkudos/deploy
sudo ./install-maintenance.sh
```

The installer resolves the current deployment directory automatically; no
family-specific or server-specific path is embedded in the service.

Only expired images from resolved task requests are removed. Text history,
balances, pending photos, and photos returned for improvement remain intact.

For a generic cron installation, run the provider-neutral maintenance command
once per night and the reminder command every 30 minutes:

```cron
15 2 * * * cd /path/to/kinkudos/deploy && docker compose exec -T app python manage.py run_maintenance
*/30 * * * * cd /path/to/kinkudos/deploy && docker compose exec -T app python manage.py run_scheduled_reminders
```

It can also be run manually on any Docker Compose host:

```bash
docker compose exec -T app python manage.py run_maintenance
docker compose exec -T app python manage.py run_scheduled_reminders
```

The legacy alias `send_lottery_reminders` still works for existing cron entries.
## Limited diagnostics access

Do not add a diagnostics-only account to the Docker group. An administrator
can instead install the root-owned `kinkudos-diagnose` command, which exposes only
the KinKudos container state and its latest 300 log lines.

```bash
sudo ./install-diagnostics.sh SYSTEM_USER
```
