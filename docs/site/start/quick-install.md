# Install on a prepared Docker server

Use this route for a **new** KinKudos installation on a server that is already prepared with Docker Engine, the Docker Compose plugin, a domain name, and an HTTPS reverse proxy such as Traefik, Caddy, or Nginx.

> **For:** Server administrator<br>
> **Difficulty:** Linux and Docker administration<br>
> **Result:** A new KinKudos installation with a first family setup

> This is an installation guide for the person who operates the server. It is
> not needed for everyday parents using KinKudos.

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

The installer downloads the latest published release, verifies its SHA256
checksum, creates the installation directory, and prepares browser setup. The
checksum confirms that the downloaded archive matches the checksum published
with the same release; it is not a separate signed attestation. The terminal
installer asks for the language, hostname, and proxy mode, then prints the
application URL and a private setup code. Open `/setup/` in the browser to
create the family name, first parent account, language, and timezone. SMTP can
be skipped and configured later in Settings.

After it finishes, check the container status and open your hostname over HTTPS
before signing in with the first parent account. If HTTPS, DNS, or a container
does not work, stop and use the deployment diagnostics instead of rerunning the
fresh installer over existing files.

## What this installer does not do

- It does not replace an existing KinKudos installation. Use [updates, backups,
  and recovery](../server/updates-and-recovery.md) for an existing server.
- It does not create a reverse proxy or DNS record for you.
- It does not send family data to GitHub or Docker Hub. The published Docker image contains the application only; your database, photos, backups, and secrets remain on your server.

## Next step

Continue with [Your first 15 minutes](first-15-minutes.md) to make the first child account useful right away.
