# Family administration

Family administration is where a parent keeps people, devices, and sensitive
family rules understandable. Most families need it only when adding someone,
changing access, or reviewing a setting — not for everyday task decisions.

> **For:** Parent administrators and parents who manage the household setup<br>
> **Result:** Clear ownership of accounts, profiles, devices, and settings

## Know the three roles

| Role | What it can do |
| --- | --- |
| **Parent** | Uses the dashboard, tasks, rewards, history, and ordinary family settings. |
| **Parent administrator** | Has all parent access plus network access, SMTP, backup credentials and manual backups, and revoking every child device. Normally this is the first parent created during setup. |
| **Child** | Uses a paired browser/PWA and four-digit PIN; sees their own data and shared catalogues, not other children’s private information. |

One adult may be both the parent administrator and server administrator, but
the server role also includes Docker, HTTPS, updates, credentials, and recovery.

## Add or retire accounts safely

In **Parents → Settings → Accounts**, give each
adult a separate parent account. Do not share passwords. An email address is
needed for password recovery when SMTP is configured.

Removing a parent deactivates that account while preserving its history. The
last active parent cannot be removed. Removing a child likewise deactivates the
profile and preserves its history; it does not transfer that child’s data to
another child.

## Profile, device, and PIN are different

- A **child profile** contains the child’s name, theme, avatar, spendable
  balance, credit, birthday, scratch-ticket setting, and History.
- A **paired device** is a specific browser, phone, tablet, or installed PWA
  allowed to display child profiles.
- A **PIN** is the child’s four-digit sign-in step on a paired device.

Pairing a new browser does not create a new child. Resetting a PIN does not
pair a device. See [pair a child device](start/pair-a-child-device.md) for the
safe 10-minute pairing-link process.

## Sensitive settings are optional

Network allowlists, SMTP, and remote backups are not required for daily tasks
and rewards. Review the [parent settings guide](parents/settings.md) before
changing them. A parent administrator must confirm their own password before
changing sensitive configuration.

## Feedback stays inside the family

Parents and children can save a private idea or problem report in the app.
It stays on the family server; it is not sent to the KinKudos maintainer.
Use GitHub Issues only for reproducible software bugs and remove all private
family data first.

[Parent settings →](parents/settings.md) · [Accounts and devices →](security/accounts-and-devices.md) · [Lietuviškai](family-administration.lt.md)
