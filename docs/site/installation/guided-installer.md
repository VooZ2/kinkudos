---
title: KinKudos guided server installer
description: Install a verified KinKudos release on a prepared Linux server, then create the first parent account securely in the browser.
---

# Guided server installer

Use this method only for a **new, empty installation** on a server that already has:

- 64-bit AMD64 or ARM64 Linux;
- Docker Engine and the Docker Compose plugin;
- a non-root deployment user with Docker access;
- a hostname resolving to the server;
- an HTTPS reverse proxy such as Caddy, Nginx, Nginx Proxy Manager, or Traefik.

The installer does not install Docker or create the reverse proxy. It refuses a non-empty installation root and must not be used to update an existing installation.

!!! warning "Docker access is privileged"
    Docker access effectively grants administrative control of the server. Use a dedicated deployment account, but treat it as privileged and protect its credentials.

## Review and run the installer

You can [inspect the installer source](https://kinkudos.app/install.sh) before running it. Then sign in as the deployment user and run:

```bash
curl -fsSL https://kinkudos.app/install.sh -o /tmp/kinkudos-install.sh \
  && sh /tmp/kinkudos-install.sh
```

The bootstrapper discovers the latest release, downloads its archive and SHA256 file, verifies the checksum and archive paths, creates `/opt/kinkudos`, and starts the versioned setup script.

Choose:

1. installation language (`en` or `lt`);
2. the exact public hostname;
3. the already prepared proxy mode: `host`, `traefik`, or `container`.

The installer generates server secrets, writes the local `.env`, selects the proxy overlay, checks directory ownership, pulls the image pinned to the selected KinKudos release, and starts `app` and `backup-agent`.

## Expected result

At the end you should see container status followed by:

```text
Open https://family.example.com/setup/ and enter this setup code in the browser:
...
```

Keep the setup code private. Continue with [First-time web setup](first-time-setup.md). The terminal does not ask for the family name, parent password, or child PINs.

If the containers do not start, run from `/opt/kinkudos/deploy`:

```bash
docker compose ps
docker compose logs --tail=100 app
```

Remove secrets and family information before sharing logs. See [Troubleshooting](../troubleshooting.md) for safe checks. Existing installations must follow [Updating KinKudos](updating.md).
