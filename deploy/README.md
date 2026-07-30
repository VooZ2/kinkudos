# Deployment

This directory lives next to the application source directory on the server.
The suggested layout is:

```text
kinkudos/
├── app/
├── deploy/
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
- `restic.env` (only when external `restic` backups are used);
- `smtp_password` (only when email is enabled).

Secret files must be owned by the deployment administrator and have `0600`
permissions. Never commit `.env` or the `secrets` directory.

## Installation

Prerequisites:

- a 64-bit ARM or x86 Linux host with Docker Engine and Docker Compose;
- an existing Traefik instance attached to an external Docker network named
  `web`;
- a hostname routed to the host;
- access to the chosen release archive and its SHA256 checksum. When using
  GitHub CLI with a private repository, authenticate an account that can read
  that repository.

Place the release source in `app` and this directory beside it as shown above.
Set `KINKUDOS_HOSTNAME` and, when needed, `KINKUDOS_ALLOWED_NETWORKS` in
`deploy/.env`, then run:

```bash
cd /path/to/kinkudos/deploy
./bootstrap.sh
```

The installer asks for English or Lithuanian, hostname, allowed private
networks, and whether to create the first family. Family setup asks for the
first parent credentials, family name, and child profiles. It generates
missing Django, VAPID, backup-agent, and `restic` secrets, creates `.env`, and
builds the images. Existing secrets are not overwritten.

For an unattended English installation, set:

```bash
KINKUDOS_DEFAULT_LANGUAGE=en ./bootstrap.sh
```

Use `lt` instead of `en` for Lithuanian. Users can still switch language in the
web interface; their choice is saved on that device.

If initial family creation was skipped:

```bash
docker compose exec app python manage.py setup_family --language en
```

## Updating from a release archive

Run these commands from the deployment root (the directory containing
`app`, `deploy`, `data`, and `secrets`). Replace `OWNER/REPOSITORY` and the
version with the release you want to install:

```bash
version=26.1.0
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

The updater validates the checksum and release metadata, builds and smoke-tests
the image, backs up the live database, switches the app only after those checks
pass, and verifies container health. The release archive never contains
`deploy/.env`, runtime data, uploads, backups, or secrets.

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

To request the same verified backup from the server:

```bash
./backup.sh
```

Backups run automatically once per day after 03:00 server time. Set
`KINKUDOS_BACKUP_HOUR` in `deploy/.env` to choose another hour. Local database
copies and remote daily snapshots are retained for 31 days. A successful run
includes `restic check`.

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

Signed-in parents and children can submit a problem or suggestion from the
floating bug button. KinKudos saves the report before attempting email
delivery. Parents can review and update report statuses in Settings even if
SMTP is unavailable. Optional screenshots are private WebP files; only
screenshots from resolved reports are removed after the retention period
selected in Settings.

## Daily image cleanup

KinKudos keeps task photos and resolved-feedback screenshots for the periods
selected in the parent settings. On a systemd-based Docker host, enable the
daily cleanup job after deployment:

```bash
cd /path/to/kinkudos/deploy
sudo ./install-maintenance.sh
```

The installer resolves the current deployment directory automatically; no
family-specific or server-specific path is embedded in the service.

Only expired images from resolved task requests are removed. Text history,
balances, pending photos, and photos returned for improvement remain intact.

For a generic cron installation, run the same provider-neutral Django command
inside the application container once per night:

```cron
15 2 * * * cd /path/to/kinkudos/deploy && docker compose exec -T app python manage.py purge_task_evidence
```

It can also be run manually on any Docker Compose host:

```bash
docker compose exec -T app python manage.py purge_task_evidence
```

## Limited diagnostics access

Do not add a diagnostics-only account to the Docker group. An administrator
can instead install the root-owned `kinkudos-diagnose` command, which exposes only
the KinKudos container state and its latest 300 log lines.

```bash
sudo ./install-diagnostics.sh SYSTEM_USER
```
