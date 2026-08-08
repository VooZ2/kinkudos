---
title: Install KinKudos on a Hostinger VPS
description: Deploy KinKudos 26.6.3 with Hostinger Docker Manager, the managed Traefik reverse proxy, HTTPS, and a persistent named volume.
---

# Install KinKudos on a Hostinger VPS

This is the simplest supported Hostinger route. It uses Hostinger's **Ubuntu
24.04 with Docker** VPS template, Docker Manager, the Traefik reverse proxy
installed with that template, and the dedicated KinKudos Compose file from
the `26.6.3` release.

The KinKudos Compose definition uses the public `vooz2/kinkudos:26.6.3` image
and one persistent named volume for the application database, media, and
runtime secrets. Hostinger VPS is paid and self-managed: you remain
responsible for the VPS, domain, updates, and snapshots.

## 1. Before you start

You need:

- a Hostinger account and a VPS created from Hostinger's **Ubuntu 24.04 with
  Docker** template;
- a domain or subdomain you control;
- access to that domain's DNS records;
- the VPS public IPv4 address;
- a password manager for the private setup code, parent credentials, and other secrets.

KinKudos is free. Hostinger is an external hosting provider and is not an
official KinKudos partner.

[Start on Hostinger](https://www.hostinger.com/vps/docker-hosting?compose_url=https://raw.githubusercontent.com/VooZ2/kinkudos/main/deploy/hostinger/compose.yaml&REFERRALCODE=LKIGEDIMICSU#pricing)

> **Referral offer:** The link may provide a discount or other benefit on eligible
> Hostinger services, depending on the current offer. I may also receive a
> commission at no additional cost to you. Hostinger is optional and is not an
> official KinKudos partner.

The link opens Hostinger’s Docker VPS selection and passes the KinKudos Compose
URL to Docker Manager. After choosing a VPS, provide your hostname and private
setup token, then finish the first family setup in the browser.

## 2. Point your domain to the VPS

Create an `A` record for the hostname you want to use, for example
`family.example.com`, pointing to the VPS public IPv4 address. Allow DNS time
to propagate.

The Docker template installs Traefik for you. Keep that Traefik application
running and leave its HTTP/HTTPS entrypoints enabled. Do not publish KinKudos
port `8000` directly; Traefik must be the public entry point.

## 3. Open the manual Compose editor

In **Docker Manager → Applications**, open **Compose** and select **Compose
manually**. Do not select **Compose from URL**: that screen does not provide
the KinKudos variables before the project is created.

![Hostinger Docker Manager Compose menu with Compose manually selected](../assets/hostinger-compose-menu.png)

Set **Application name** to:

```text
kinkudos
```

Open the **.yaml editor**. Replace its complete contents, including the initial
`services:` line, with the exact release file from:

```text
https://raw.githubusercontent.com/VooZ2/kinkudos/v26.6.3/deploy/hostinger/compose.yaml
```

You can inspect the same file in
[GitHub](https://github.com/VooZ2/kinkudos/blob/v26.6.3/deploy/hostinger/compose.yaml).
It defines the `app` service, the `vooz2/kinkudos:26.6.3` image, the Hostinger
Traefik labels, and the named volume `kinkudos-data`.

## 4. Add the two required values

Return to **Visual editor**, expand **Environment**, and add these two names
and values:

```text
KINKUDOS_HOSTNAME=family.example.com
KINKUDOS_SETUP_TOKEN=<long-private-setup-code>
```

Enter the hostname without `https://` or a trailing slash. Generate a long
random setup code in a password manager or with:

```bash
openssl rand -hex 32
```

Keep the setup code private; it is needed only to create the first family and
parent account. Do not reveal either value in screenshots. Do not add other
variables unless you have a specific supported configuration need.

![Hostinger Compose application with the KinKudos image and masked required variables](../assets/hostinger-compose-environment.png)

## 5. Deploy and complete browser setup

Click **Save and deploy** below the Environment values. Wait until
`kinkudos-app-1` shows **Running**. Traefik should then route the hostname,
redirect HTTP to HTTPS, and obtain the Let's Encrypt certificate.

![A running KinKudos container in Hostinger Docker Manager](../assets/hostinger-kinkudos-running.png)

Open:

```text
https://family.example.com/setup/
```

Enter the setup code and create the family and first parent administrator in
the browser. Then sign in and confirm that the parent dashboard loads.

## 6. Persistent data and maintenance

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
