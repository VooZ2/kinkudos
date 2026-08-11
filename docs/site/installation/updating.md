---
title: Update KinKudos safely
description: Back up a KinKudos installation, install a verified release, check container health, and recover safely when an update fails.
---

# Update KinKudos safely

Only the latest published release is supported. Read its [release notes](https://github.com/VooZ2/kinkudos/releases), keep a tested backup, and never replace persistent `data` or `secrets` with files from a release archive.

## Before updating

1. Confirm the current installation is healthy.
2. Confirm a recent remote backup and keep the repository password offline.
3. Make sure there is sufficient free disk space.
4. Record the currently installed version.
5. Read release-specific actions.

## Supported update

Use the release archive, SHA256 file, and `install-release.sh` procedure from the [technical deployment reference](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.md#updating-an-existing-installation). Run it from the deployment root, not from an arbitrary Compose copy.

The updater verifies release metadata and checksum, pulls and smoke-tests the pinned image, checks directory ownership, creates a consistent database backup, starts the new app and backup agent, waits for health, verifies migrations and version, and refreshes versioned management helpers. It preserves `.env`, `data`, uploads, backups, and secrets.

On Hostinger, use Docker Manager's supported Update action and verify the
managed Traefik route and HTTPS result afterward. Create a VPS snapshot first.

## Verify the result

```bash
cd /opt/kinkudos/deploy
docker compose ps
docker compose logs --tail=100 app
```

Open KinKudos, confirm the displayed version, sign in, and check a normal parent
page. For Hostinger, also verify the Docker Manager application status, Traefik
route, HTTPS URL, login, and family data in the browser.

## If an update fails

If the new container never becomes healthy, the updater stops and does not
restore or restart the previous image automatically. The new image may already
have applied database migrations. A consistent database backup was created
before the replacement, but it is not automatically restored. Preserve the
updater output and container logs, do not start an older image or overwrite the
live database with an older copy without a separately verified recovery plan,
and use [Troubleshooting](../troubleshooting.md).
