---
title: Stop or uninstall KinKudos
description: Stop KinKudos containers without accidentally deleting family data, secrets, backups, or persistent volumes.
---

# Stop or uninstall KinKudos

Stopping containers and deleting family data are different operations. Make and verify a backup before either.

For a Hostinger Docker Manager application, use Docker Manager's stop or
remove action without deleting the `kinkudos-data` named volume. This removes
containers while retaining the application database, media, and runtime
secrets. Re-import the same Compose definition if you need to recreate it.

For a generic deployment, use `docker compose down` from its `deploy` directory. Do not add `-v` unless you have independently identified every volume and intentionally want to destroy it.

Permanent deletion of `/opt/kinkudos`, bind-mounted data, secrets, backups, or Docker volumes is irreversible and is not included in this guide. Resolve and verify exact paths first; never use a broad recursive command or an unresolved variable.
