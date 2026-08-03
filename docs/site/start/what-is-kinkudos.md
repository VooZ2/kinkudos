# What is KinKudos?

KinKudos is a private, self-hosted app for one family. Children complete tasks, earn points, and request rewards; parents review requests and decide what happens next.

There are no ads, no built-in analytics, and no shared public family space. The database, photos, and credentials stay with the person operating the family’s installation.

```text
Task → submission → parent decision → points → reward or goal → history
```

## The main features

| Feature | How it works |
| --- | --- |
| **Tasks** | Children can choose a catalogue task and submit it, optionally with a photo. Parents approve, ask for improvements, or reject it. Parents may also award a confirmed task directly. |
| **Daily assigned tasks** | Parents can send a child a set of tasks for today. Completing each one immediately adds the recorded points. |
| **Rewards and goals** | Children request rewards or suggest a new reward/savings goal. Parents decide and set the final point cost. Goals show progress against the child’s normal balance. |
| **Points and history** | Every addition, deduction, gift, ticket purchase, or correction creates an append-only history entry. Corrections are new entries, never hidden edits. |
| **Credit** | A parent can allow a child to spend into a negative balance up to a chosen lower limit. New reward requests pause once half of that credit is used. |
| **Lottery tickets** | An optional family-controlled scratch ticket has a configurable cost, per-child weekly limit, transparent outcomes, and no loss below the credit limit. |
| **Child worlds** | Children can select built-in themes, upload an avatar, choose daily random themes, change their own PIN, and suggest rewards or goals. |
| **Notifications** | Parents and children can opt into browser notifications for relevant decisions and requests. On iPhone and iPad, the app must first be installed to the Home Screen. |
| **Private feedback** | Parents and children can save a private idea or problem report inside KinKudos, with an optional screenshot. |

## Who uses it

- **Parent** accounts make everyday decisions and see the family dashboard.
- The **parent administrator** has the same parent access plus sensitive configuration: network restrictions, SMTP, remote backup credentials, manual backups, and revoking all child devices.
- **Child** profiles use a paired device and four-digit PIN. A child sees only their own information and the family’s shared catalogues.
- The **server administrator** operates the server, HTTPS proxy, updates, and recovery. In a small household this may be the same person as the parent administrator.

## What KinKudos does not do

KinKudos is not a bank, parental-monitoring tool, or social network. It does not track a child’s location, read device content, scan private messages, or publish family activity. It helps a family agree on everyday tasks and rewards in one place.

[Quick install →](../installation/guided-installer.md) · [Your first 15 minutes →](first-15-minutes.md) · [Lietuviškai](what-is-kinkudos.lt.md)
