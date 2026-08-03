# Security policy

## Reporting a vulnerability

Please report a suspected KinKudos security vulnerability privately to
[security@kinkudos.app](mailto:security@kinkudos.app). Do not open a public
GitHub Issue for a vulnerability that has not yet been patched.

Include, where possible:

- the affected KinKudos version;
- clear reproduction steps;
- the expected impact; and
- any suggested mitigation.

While investigating a report, do not access, modify, retain, or publish other
users' data. Do not include passwords, secrets, databases, backup files,
private family information, photos, or unredacted logs in a report.

KinKudos is a community project maintained on a best-effort basis. Receipt,
assessment, and resolution times are not guaranteed. Confirmed issues are
assessed and fixed on a best-effort basis, normally for the latest published
release.

There is no bug bounty or other monetary reward program.

Please wait to disclose a vulnerability publicly until a fix or mitigation is
available and disclosure has been coordinated with the maintainer.

## Supported versions

Only the latest published KinKudos release is supported. Before requesting
help, update to that release. Security fixes are normally released only for
the latest version; older releases may not receive fixes, compatibility
updates, or support.

For ordinary product bugs and feature requests, use
[GitHub Issues](https://github.com/VooZ2/kinkudos/issues). Do not use GitHub
Issues to report an unpatched security vulnerability.

## Deployment security notes

- Complete a new public installation promptly over HTTPS and keep its setup
  code private. Setup permanently locks after the first family administrator
  is created; attempts to bypass that lock are security issues.
- Use a strong, unique parent password and save the one-time recovery code
  outside the server in a password manager.
- Keep SMTP credentials, `.env`, databases, uploads, backups, setup and
  recovery codes, and server secrets out of Git, screenshots, Issues, and
  unredacted logs.
- CLI recovery and emergency-account commands grant sensitive access. Run them
  only from the correct deployment and after making a backup.
- Keep the remote-backup repository password offline and test restoration in
  an isolated environment before depending on a backup.

Report any setup-bypass, first-administrator takeover, secret-disclosure, or
authentication-bypass vulnerability privately using the address above.
