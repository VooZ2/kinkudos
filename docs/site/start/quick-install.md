# Quick install

Use this route for a **new** KinKudos installation on a server that is already prepared with Docker Engine, the Docker Compose plugin, a domain name, and an HTTPS reverse proxy such as Traefik, Caddy, or Nginx.

> This is an installation guide for the person who operates the server. It is not needed for everyday parents using KinKudos.

## Before you start

Check that all of the following are ready:

- a 64-bit Linux server (AMD64 or ARM64) that you control;
- Docker Engine and the `docker compose` plugin;
- a hostname pointing at the server, for example `family.example.com`;
- an HTTPS reverse proxy configured to accept the hostname; and
- a normal server user with permission to use Docker. Do not run the installer as `root`.

## Run the installer

On the prepared server, run:

```bash
curl -fsSL https://kinkudos.app/install.sh -o /tmp/kinkudos-install.sh && sh /tmp/kinkudos-install.sh
```

The installer downloads the latest published release, verifies its SHA256 checksum, creates the installation directory, and opens the guided setup. It asks for the language, hostname, proxy mode, family name, first parent account, and optional child profiles.

After it finishes, open your hostname over HTTPS and sign in with the first parent account.

## What this installer does not do

- It does not replace an existing KinKudos installation. Use the [installation and maintenance guide](../deployment-and-maintenance.md) for updates.
- It does not create a reverse proxy or DNS record for you.
- It does not send family data to GitHub or Docker Hub. The published Docker image contains the application only; your database, photos, backups, and secrets remain on your server.

## Next step

Continue with [Your first 15 minutes](first-15-minutes.md) to make the first child account useful right away.
