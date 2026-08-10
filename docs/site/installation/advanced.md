---
title: Advanced KinKudos deployment
description: Integrate KinKudos with an existing Caddy, Nginx, Traefik, or Nginx Proxy Manager environment while preserving proxy trust and private ports.
---

# Advanced deployment

Use this page when you already operate Docker and an HTTPS proxy. KinKudos does not require a provider-specific image: all methods use the same pinned application and backup-agent images. Start with [Choose the proxy mode](docker-compose.md#choose-the-proxy-mode-before-running-the-installer) before running `bootstrap.sh`.

- Host Caddy or Nginx: use the `host` overlay and proxy to `127.0.0.1:8000`.
- Traefik: use the provided Traefik overlay and the exact external network.
- Nginx Proxy Manager or another container proxy: use the `container` overlay, service `app`, port `8000`, and the configured external network.

Forward `Host`, `X-Forwarded-Proto`, and client IP headers. Restrict `KINKUDOS_TRUSTED_PROXIES` to the real proxy address or Docker subnet; never trust the internet. Validate `docker compose config` before starting and keep `data`, backups, and secrets outside release source.

The complete commands and proxy examples are maintained in the [technical deployment reference](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.md#reverse-proxy-and-client-ips).
