---
title: Install KinKudos on a Hostinger VPS
description: Deploy KinKudos 26.5.2 with Hostinger Docker Manager, the managed Traefik reverse proxy, HTTPS, and a persistent named volume.
---

# Install KinKudos on a Hostinger VPS

This is the simplest supported Hostinger route. It uses a Hostinger VPS with
Docker Manager, Hostinger's managed Traefik reverse proxy, and the dedicated
KinKudos Compose file from the `26.5.2` release.

The KinKudos Compose definition uses the public `vooz2/kinkudos:26.5.2` image
and one persistent named volume for the application database, media, and
runtime secrets. Hostinger VPS is paid and self-managed: you remain
responsible for the VPS, domain, updates, and snapshots.

## 1. Before you start

You need:

- a Hostinger account and a VPS with Docker Manager;
- a domain or subdomain you control;
- access to that domain's DNS records;
- the VPS public IPv4 address;
- a password manager for the private setup code, parent credentials, and other secrets.

KinKudos is free. Hostinger is an external hosting provider and is not an
official KinKudos partner.

[View Hostinger VPS options](https://www.hostinger.com/lt?REFERRALCODE=LKIGEDIMICSU)

> **Affiliate disclosure:** This is a referral link. If you purchase through it,
> the maintainer may receive a commission at no additional cost to you.

## 2. Point your domain to the VPS

Create an `A` record for the hostname you want to use, for example
`family.example.com`, pointing to the VPS public IPv4 address. Allow DNS time
to propagate.

In Hostinger, keep the managed Traefik and its HTTP/HTTPS entrypoints enabled.
Do not publish KinKudos port `8000` directly; Traefik must be the public entry
point.

## 3. Import the KinKudos Compose file

In Docker Manager, create a new Compose application and import the exact file
from the repository:

```text
deploy/hostinger/compose.yaml
```

You can inspect the file in [GitHub](https://github.com/VooZ2/kinkudos/blob/main/deploy/hostinger/compose.yaml).
It defines the `app` service, the `vooz2/kinkudos:26.5.2` image, the Hostinger
Traefik labels, and the named volume `kinkudos-data`.

Before deploying, provide the two values required by that Compose file:

```text
KINKUDOS_HOSTNAME=family.example.com
KINKUDOS_SETUP_TOKEN=<long-private-setup-code>
```

Use your real hostname and generate a long random setup code. Keep the setup
code private; it is needed only to create the first family and parent account.
Do not invent additional variables unless you have a specific supported
configuration need.

## 4. Deploy and complete browser setup

Click **Deploy** in Docker Manager. Hostinger's managed Traefik should route
the hostname, redirect HTTP to HTTPS, and obtain the Let's Encrypt certificate.
Open:

```text
https://family.example.com/setup/
```

Enter the setup code and create the family and first parent administrator in
the browser. Then sign in and confirm that the parent dashboard loads.

## 5. Persistent data and maintenance

The named volume `kinkudos-data` contains the SQLite database, uploaded media,
and runtime secrets. Container restart, Compose force-recreate, and VPS restart
must not remove it. Do not delete the volume when recreating the Compose
application.

Before a significant change, create a Hostinger VPS snapshot. A snapshot
restores the complete VPS state. This path was tested with clean deployment,
HTTPS, first-time setup, persistent data, container and VPS restarts, Compose
recreate, Docker Manager Update, snapshot creation, and snapshot restore.

A VPS snapshot is not a portable application-level backup for every scenario.
Keep a separate, tested KinKudos backup strategy when you need portability or
recovery outside Hostinger.

The Hostinger Compose file intentionally does not include KinKudos's generic
`backup-agent`, Restic configuration, or additional backup secrets. For later
Hostinger maintenance, use Docker Manager's supported update action and create
a snapshot first. Do not assume that a new Compose definition or image tag is
applied automatically.

For the browser setup details, see [First-time web setup](first-time-setup.md).
