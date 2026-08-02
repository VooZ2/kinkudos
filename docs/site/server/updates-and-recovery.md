# Updates, backups, and recovery

Keep the server on the latest published KinKudos release. Updates and recovery
are server-administrator operations, not ordinary parent settings.

> **For:** Server administrator<br>
> **You need:** Access to the deployment directory, its secrets, and verified
> backups<br>
> **Result:** A safe update and recovery routine

## Update safely

Use the exact [existing-installation update procedure](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.md#updating-an-existing-installation).
It verifies the release checksum and metadata, backs up the live database,
checks writable-directory ownership, smoke-tests the image, and switches the
application only after those checks pass.

The update is designed to preserve the local deployment environment, runtime
data, uploads, backups, and secrets. Do not replace those paths manually with
a release archive. Read the release notes before updating and keep a known
working backup.

## Backups are protection, not a restore test

Remote encrypted backups include the family database and uploaded media. The
backup repository password is separately protected server data: keep it outside
the server. A copy stored only on the same disk as the application does not
protect against loss of that server.

Check the application’s latest successful backup date and displayed error. Take
an additional copy before a risky change if the backup service is healthy, but
do not treat “Back up now” as a restore process.

## Recovery and moving a server

The supported recovery instructions live in the deployment guide. First test a
restore in a separate, safe directory; never make the live family installation
your first restore test. You will need the backup repository password in
addition to storage access.

Moving to another server is a recovery/migration task: prepare the target
server, preserve the required secrets, restore tested data, then validate the
application and HTTPS before directing family devices to it. Do not delete the
old server until the replacement has been verified.

## When something fails

Collect the displayed error and the relevant redacted container logs, then use
the [diagnostics section](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.md)
and [quick help](../quick-help.md). Never put credentials, databases, backup
files, family data, photos, or unredacted logs in a public issue.

[Lietuviškai](updates-and-recovery.lt.md)
