# Server administration

This section is for the person who keeps the family’s KinKudos server running.
Everyday parents normally need only the application. Do not change network
restrictions, remote-backup credentials, or server configuration unless you
understand the effect and can recover access.

<div class="grid cards" markdown>

-   :material-shield-check-outline: **Before installing**

    ---

    Requirements, supported paths, HTTPS, and what self-hosting makes the
    family responsible for.

    [Prepare the server →](server/before-installing.md)

-   :material-download-outline: **Install on a prepared server**

    ---

    Use the guided installer only for a fresh KinKudos installation.

    [Open quick install →](start/quick-install.md)

-   :material-sync: **Update and recover**

    ---

    Keep the latest release, protect backups, test recovery, and diagnose a
    problem without exposing family data.

    [Open update and recovery guide →](server/updates-and-recovery.md)

-   :material-book-open-page-variant-outline: **Detailed deployment reference**

    ---

    Exact commands for Docker, Ubuntu, Caddy/Nginx/Traefik, updates, and
    diagnostics are kept with the release source.

    [Open deployment guide ↗](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.md)

</div>

## Server responsibilities at a glance

| Area | Administrator must decide or maintain |
| --- | --- |
| **Domain and HTTPS** | DNS routing, certificate-capable reverse proxy, and protected public access. |
| **Docker and updates** | Current release, container health, and host maintenance. |
| **Email** | Optional SMTP credentials for password recovery and feedback notices. |
| **Network access** | Optional IP allowlists; test carefully to avoid locking out the family. |
| **Backups** | Remote storage, repository password, recent success, and a tested restore. |

[Quick help →](quick-help.md) · [Lietuviškai](deployment-and-maintenance.lt.md)
