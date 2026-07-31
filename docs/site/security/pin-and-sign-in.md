# PINs and sign-in protection

KinKudos uses two different sign-in methods because parents and children need different levels of access.

## Parent sign-in

Each parent has a separate username and password. Passwords must be at least 12 characters and must pass Django’s checks against common, all-numeric, and username-like passwords. Parent passwords are stored as secure password hashes, not readable text.

Use one account per adult. Do not share a parent password with a child, even if the child knows the device PIN.

Parents can change their own account details in **Parents → Settings → Parent accounts**. Password-reset email is available only after an administrator has configured SMTP.

### Reset a parent password

On the parent sign-in page, select **Forgot password?**, enter the email address of an active parent account, then use the link sent by email to choose a new password. This page is intentionally unavailable while SMTP email is disabled. If no message arrives, first check the spam folder, then ask the parent administrator to verify the SMTP settings; do not create a replacement account merely to regain access.

## Child PIN logic

A child signs in with exactly four digits, but only from a [paired device](../start/pair-a-child-device.md). The PIN is stored as a secure hash and is never shown to parents or children after it is set.

KinKudos protects the PIN screen in several ways:

- a device must be paired before it can even list child profiles or accept a PIN;
- incorrect attempts are limited by child profile, device, IP address, and the whole site;
- after five incorrect attempts for one child profile, that profile is locked for five minutes; and
- a parent can use **Unlock profile** on that child’s parent card instead of waiting.

Changing the PIN immediately makes the old PIN unusable. Revoking a device signs out child access on that device; the child must use a newly paired device and the current PIN to return.

## A simple family rule

Treat the child PIN as private, not as a shared family code. Pair only devices that stay under family control. If a device is lost, sold, borrowed for a long time, or used by someone outside the family, revoke it immediately.

## Parent administrator

The first parent created during setup is the parent administrator. This account has the normal parent abilities plus the sensitive controls: network restrictions, SMTP, remote backup credentials, manual backups, and revoking all child devices. Other parent accounts can still use the everyday parent menu and see backup status.

[Accounts and devices →](accounts-and-devices.md) · [Network access →](network-access.md)
