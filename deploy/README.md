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
- `restic.env` (only when external `restic` backups are used);
- `smtp_password` (only when email is enabled).

Secret files must be owned by the deployment administrator and have `0600`
permissions. Never commit `.env` or the `secrets` directory.

## Installation

```bash
cd /path/to/kinkudos/deploy
./bootstrap.sh
```

The installer asks whether the installation language is English or Lithuanian,
generates missing Django, VAPID, and `restic` secrets, creates `.env`, builds
the image, and optionally creates the first family. Existing secrets are not
overwritten.

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

## Backups

Initialize the `restic` repository before the first external backup:

```bash
docker compose --profile backup run --rm restic init
```

Then run:

```bash
./backup.sh
```

The retention policy and scheduler should be selected by the server
administrator. The project scripts are provider-neutral and use a standard
`restic` repository.

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

Email is disabled by default until SMTP is configured.

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
