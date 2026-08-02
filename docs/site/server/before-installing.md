# Before installing KinKudos

This guide is for the person who will operate the family’s server. KinKudos is
not a hosted service: the server administrator is responsible for the server,
HTTPS, credentials, updates, and recovery.

> **For:** Server administrator<br>
> **Difficulty:** Linux and Docker administration<br>
> **Result:** A prepared, safe starting point for installation

## Required before the installer

- a 64-bit ARM or x86 Linux host and an administrator account with `sudo`;
- Docker Engine and the Docker Compose plugin;
- a hostname routed to that host;
- an HTTPS reverse proxy, such as Caddy, Nginx, Nginx Proxy Manager, Traefik,
  or an equivalent setup; and
- access to the KinKudos release archive, its SHA256 checksum, and the public
  Docker image.

No formal CPU, memory, or disk minimum is established. Size the server for
your family’s database, uploaded photos, backup process, operating system, and
headroom for updates. Do not expose KinKudos’s application port directly to
the internet; terminate public HTTPS at the reverse proxy.

## Supported installation paths

| Situation | Status |
| --- | --- |
| Fresh 64-bit Linux server with Docker Compose and a supported HTTPS proxy | Documented installation path. |
| Host-installed Caddy or Nginx | Documented reverse-proxy mode. |
| Container proxy or Traefik | Documented reverse-proxy mode. |
| Other Linux distributions, NAS products, custom proxies, or unusual networks | May work, but community best-effort only. |

Keep an existing SSH session open while changing network or proxy settings.
Confirm DNS reaches the server before expecting an HTTPS certificate to be
issued.

## Next step

Use the [prepared Docker-server installer](../start/quick-install.md), then
read the full [deployment guide](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.md)
before making custom changes.

[Lietuviškai](before-installing.lt.md)
