---
title: Configure optional SMTP email
description: Configure and verify optional KinKudos SMTP settings for parent password recovery and private feedback notification emails.
---

# SMTP configuration

SMTP is optional. KinKudos tasks, points, rewards, child access, and private in-app feedback work without it. SMTP enables parent password-recovery email and optional notifications when private feedback is saved.

You can configure SMTP during [first-time setup](../installation/first-time-setup.md) or later as the parent administrator under **Parents → Settings → Email settings**. Later changes require the administrator’s current KinKudos password.

| Field | Meaning |
|---|---|
| **SMTP server** | Outgoing-mail hostname, such as `smtp.example.com`, without a URL path. |
| **Port** | Provider-specified port; commonly 587 for STARTTLS or 465 for implicit SSL/TLS. |
| **Security** | Choose STARTTLS/TLS, SSL/TLS, or none exactly as the provider requires. Never choose none across an untrusted network. |
| **Username** | SMTP login, often—but not always—the sending email address. |
| **Password** | SMTP password or provider app password. Re-enter it whenever saving changes. |
| **Sender address** | Address recipients see; the provider must normally permit it. |
| **Feedback recipient** | Optional address notified about private in-app feedback. |

KinKudos verifies the SMTP connection before saving. There is no separately documented **Send test email** action in this release. Provider requirements can change; follow the provider’s current instructions and use an app password when required.

The UI-managed configuration is stored in a permission-protected file under `secrets/smtp/`; the password is not stored in the application database and is never displayed after saving. Do not place SMTP credentials in Git, screenshots, support requests, or logs.

Advanced operators can use the release-owned `configure-email.sh` helper or supported environment fallback described in the [deployment reference](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.md#password-reset-email).
