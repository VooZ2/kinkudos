---
title: Stop or uninstall KinKudos
description: Stop KinKudos containers without accidentally deleting family data, secrets, backups, or Caddy certificate state.
---

# Stop or uninstall KinKudos

Stopping containers and deleting family data are different operations. Make and verify a backup before either.

For a recognized Hostinger installation, run as root:

```bash
/opt/kinkudos/deploy/uninstall-hostinger.sh /opt/kinkudos
```

This performs `docker compose down`. It removes the containers but deliberately retains application data, secrets, backups, installation files, and Caddy certificate volumes. Running the supported Hostinger installer again resumes the recognized installation.

For a generic deployment, use `docker compose down` from its `deploy` directory. Do not add `-v` unless you have independently identified every volume and intentionally want to destroy it.

Permanent deletion of `/opt/kinkudos`, bind-mounted data, secrets, backups, or Docker volumes is irreversible and is not included in this guide. Resolve and verify exact paths first; never use a broad recursive command or an unresolved variable.
