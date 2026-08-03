---
title: Install KinKudos on a Hostinger VPS
description: Create a Hostinger Ubuntu 24.04 Docker VPS, connect a domain, run the verified KinKudos installer with automatic Caddy HTTPS, and finish setup in a browser.
---

# Install KinKudos on a Hostinger VPS

This is the simplest supported way to start a new KinKudos server. You create a Hostinger VPS, connect your domain, run one installation command, and finish the family setup in your browser.

The installer supports Hostinger’s **Ubuntu 24.04 with Docker** template. It runs in Browser Terminal as `root`, starts KinKudos with Caddy, configures HTTPS, and prints the private setup code.

KinKudos is free. Hostinger VPS is a paid, self-managed service: you remain responsible for the VPS, domain, updates, and tested backups. Allow about 30–60 minutes, plus possible DNS propagation time.

## 1. Before you start

You need:

- a Hostinger account and payment method;
- a domain or subdomain you control;
- access to that domain’s DNS records;
- an email address for your Hostinger account;
- a password manager where you can safely store the VPS password, setup code, and recovery code.

SMTP is optional and can be configured later.

[View Hostinger VPS options](https://www.hostinger.com/lt?REFERRALCODE=LKIGEDIMICSU)

> **Affiliate disclosure:** This is a referral link. If you purchase through it, the maintainer may receive a commission at no additional cost to you. Hostinger is not required to use KinKudos, is not an official KinKudos partner, and does not receive access to your family data beyond the VPS service you operate.

Choose a **VPS**, not shared Web Hosting. Choose a plan that supports the **Ubuntu 24.04 with Docker** template. Plan names, resources, and prices may change.

## 2. Create the VPS

Create a VPS using the Hostinger **Ubuntu 24.04 with Docker** template. Do not substitute another operating system: the Hostinger installation profile validates this exact template.

Wait until hPanel reports that the VPS is running. Save its public IPv4 address and root credentials securely.

## 3. Connect your domain

Create an `A` record for the hostname you want to use, for example `family.example.com`, pointing to the VPS public IPv4 address. If DNS is managed elsewhere, create the same record with that DNS provider.

Use only a lowercase fully qualified hostname. The installer does not accept an IP address or a temporary HTTP address. DNS propagation can take time.

In the Hostinger VPS firewall, allow inbound TCP ports **80** and **443**. Keep SSH or Browser Terminal access available. Do not expose port `8000`.

Before installing, confirm from your computer that the hostname resolves to the VPS. The following command is available on Windows, macOS, and many Linux systems:

```bash
nslookup family.example.com
```

Replace the example with your real hostname. The result should contain the VPS IP.

## 4. Install KinKudos

Open Hostinger **Browser Terminal**. The supported template starts with root access, which this dedicated installer expects.

Run the public Hostinger installer:

```bash
curl -fsSL https://kinkudos.app/install-hostinger.sh \
  -o /tmp/install-kinkudos-hostinger.sh \
  && sh /tmp/install-kinkudos-hostinger.sh
```

The small installer discovers the latest published release, downloads its archive and SHA256 checksum from GitHub, verifies both the checksum and archive paths, and only then runs the release-owned Hostinger bootstrap. You may inspect the downloaded script before running it by separating the download and `sh` commands.

Enter:

1. `en` or `lt` for the application’s initial language;
2. the exact hostname created in the previous step, without `https://` or a path.

The bootstrap verifies Ubuntu, Docker and Compose versions, checks that ports 80 and 443 are free, creates `/opt/kinkudos`, generates secrets, and starts:

- the private KinKudos `app` container;
- the isolated `backup-agent`;
- Caddy on public ports 80 and 443.

Caddy redirects HTTP to HTTPS and obtains and renews the TLS certificate. Its certificate data persists across normal updates and safe container removal.

## 5. Check the result

The installer reports one of three clear states:

- **deployed and HTTPS ready** — continue immediately;
- **deployed but HTTPS pending** — KinKudos and Caddy run, but DNS or certificate issuance is not ready;
- **failed** — review the displayed reason and safe log excerpt.

For a pending certificate, confirm DNS and firewall ports 80/443, wait a few minutes, then run:

```bash
/opt/kinkudos/deploy/hostinger-healthcheck.sh /opt/kinkudos
```

When ready, the installer prints:

```text
Setup URL: https://family.example.com/setup/
Setup code: ...
```

Keep the setup code private. It remains valid only until setup completes successfully.

## 6. Complete setup in your browser

Open the printed HTTPS URL and follow [First-time web setup](first-time-setup.md). Create the first parent administrator, family name, language, timezone, and strong password. Save the recovery code shown once during setup in your password manager.

You may skip SMTP. KinKudos works without it; only email password recovery and optional feedback notification email remain unavailable. See [SMTP configuration](../administration/smtp.md) when you are ready.

## 7. Start using KinKudos

Follow [Your first 15 minutes](../start/first-15-minutes.md) to create a child, task, and reward. The [notification and PWA guide](../security/notifications-and-pwa.md) explains installation on a phone.

Before relying on the server, configure [KinKudos backups](../backups.md). A Hostinger VPS snapshot protects a different layer and does not replace an application backup.

For later maintenance use [Updating KinKudos](updating.md), [logs and diagnostics](../administration/logs.md), and [Troubleshooting](../troubleshooting.md).
