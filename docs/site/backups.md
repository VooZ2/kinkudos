---
title: KinKudos backups and data protection
description: Configure encrypted remote KinKudos backups, understand local copies and VPS snapshots, preserve recovery secrets, and prepare a safe restore test.
---

# Backups and data protection

A working backup plan protects more than a running container. KinKudos stores its SQLite database and private media under the persistent `data` directory. Server secrets and the remote-backup repository password are protected separately.

## KinKudos application backup

The isolated `backup-agent` creates a consistent SQLite online backup, includes private uploaded media, and sends encrypted snapshots through restic to Backblaze B2 or generic S3-compatible storage. Configure it as the first parent under **Settings → Backups**.

Use a dedicated bucket and restricted key. Keep an offline copy of `secrets/restic_password`; without it, encrypted snapshots cannot be restored. Backups run daily after the configured hour, local DB copies and remote daily snapshots are retained for 31 days, and a successful run includes `restic check`. A failed scheduled attempt is not recorded as that day's success; it is retried later the same day with bounded backoff, and a successful scheduled run is not repeated that day.
Local SQLite backup copies and KinKudos-managed backup/state storage are protected with owner-only filesystem permissions.

The parent administrator can request **Back up now**, or the server administrator can run from `deploy`:

```bash
./backup.sh
```

Check the UI’s latest-success time and `backup-agent` logs. A green status is evidence of a recent successful run, not proof that your recovery procedure works.

## VPS backup or snapshot

A hosting-provider backup or snapshot captures a broader server layer. It may help after whole-VPS damage, but it does not replace KinKudos’ encrypted application backup, and restoring it may overwrite the complete VPS. Review the provider’s current retention, expiry, and restore warnings.

Use both layers when practical, especially before an update.

## Restore

Restore is deliberately not available in the web UI. It can overwrite live family data and requires the repository password, matching secrets, correct ownership, and version compatibility.

The project has not yet published a one-command automated restore. Do not experiment on the live installation. First restore a snapshot into a separate test directory or isolated test server, verify the database, media, sign-in, version and container health, and only then plan a controlled live recovery. The detailed [restore page](backups/restore.md) records the verified boundaries and remains conservative until the complete procedure passes release testing.
