---
title: Recover a KinKudos parent password
description: Reset a parent password by email when SMTP works or use the family recovery code from the server CLI.
---

# Parent password recovery

## Recover by email

When SMTP is enabled, select **Forgot password?** on parent sign-in, enter the active parent account’s email address, and use the emailed link. Check spam and the configured sender before assuming the account is missing.

## Recover from the server

If email is unavailable, use the family recovery code shown once and saved during first-time setup. The code remains valid until it is rotated. Make a backup first, then run interactively from `deploy`:

```bash
docker compose exec app python manage.py reset_parent_password --username PARENT_USERNAME
```

Replace `PARENT_USERNAME` with the exact sign-in name. The command asks for the recovery code and the new password without echoing them, applies Django password validation, and invalidates old sessions after the password changes.

Do not publish the recovery code, include it in a shell argument, or store it on the server beside the database. If the code was not saved, use the separately controlled [emergency administrator](emergency-admin.md) procedure rather than trying to unlock `/setup/`.
