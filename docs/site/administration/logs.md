---
title: KinKudos logs, diagnostics, and health checks
description: Check KinKudos and backup-agent status, collect safe logs, and diagnose Docker Manager or reverse-proxy problems without exposing secrets or family data.
---

# Logs, diagnostics, and health checks

Run commands from the installation’s `deploy` directory.

## Container status

```bash
docker compose ps
```

`app` should become healthy. In the generic Compose deployment, `backup-agent`
should also be running. Hostinger Docker Manager deployments use the managed
Traefik service outside this Compose file.

For Hostinger, use Docker Manager to check the application and managed Traefik
route, then open the HTTPS URL in a browser.

## Recent logs

```bash
docker compose logs --tail=100 app
docker compose logs --tail=100 backup-agent
```

For a restricted support account, the server administrator can install the root-owned `kinkudos-diagnose` helper instead of granting Docker-group access. See the technical deployment reference for installation.

Before sharing output, remove usernames, email addresses, domains when private, IP addresses when sensitive, family names, request content, and any token or credential. Never send `.env`, databases, backups, secrets, setup or recovery codes, private photos, or unredacted logs.

## Safe restart

```bash
docker compose restart app
docker compose ps
```

Do not delete volumes or host data to fix a startup error. Preserve the original error and continue with [Troubleshooting](../troubleshooting.md).
