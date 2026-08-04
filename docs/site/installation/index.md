---
title: Install KinKudos — choose a self-hosting method
description: Compare the supported KinKudos installation methods, required skills, server responsibilities, and the browser-based first-time setup.
---

# Choose your installation method

KinKudos is self-hosted: every installation serves one family and runs on a Linux server controlled by the family or its chosen administrator. The application is free, but a VPS or other hosting service may cost money.

Whichever method you choose, the process has two distinct parts:

1. prepare the server and start the KinKudos containers;
2. open `/setup/` and create the family and first parent account in a browser.

## Compare the available methods

| Method | Best for | Terminal | What you maintain |
|---|---|---:|---|
| [Hostinger VPS](hostinger.md) | People who want the simplest supported Hostinger VPS route | One command in Browser Terminal | VPS, updates, and backups |
| [Guided server installer](guided-installer.md) | A prepared Linux server with Docker and HTTPS proxy | Yes | The complete server |
| [Docker Compose](docker-compose.md) | Experienced self-hosters, NAS users, or custom proxy setups | Yes | Compose, secrets, proxy, storage, and updates |
| [Advanced deployment](advanced.md) | Existing Traefik/Nginx Proxy Manager networks or unusual Linux layouts | Yes | All integration decisions |

!!! warning "Before you install"
    Generic installations need a 64-bit AMD64 or ARM64 Linux server, Docker Engine, Docker Compose, a hostname, and an HTTPS reverse proxy. The Hostinger path uses Hostinger Docker Manager and its managed Traefik proxy. Never expose KinKudos port `8000` to the internet.

After the containers start, continue with [First-time web setup](first-time-setup.md).
