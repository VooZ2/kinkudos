---
title: Create an emergency KinKudos administrator
description: Create a temporary Django superuser only when every normal KinKudos parent recovery route is unavailable.
---

# Create an emergency administrator

Use this only when an initialized family has no usable parent administrator and both email and recovery-code reset are unavailable. It does not reopen first-time setup or repair missing family data.

1. Create and verify a backup.
2. Restrict server access to a trusted administrator.
3. From the `deploy` directory run:

```bash
docker compose exec app python manage.py createsuperuser
```

The command creates a Django superuser. KinKudos parent access is based on Django user accounts, so this account can sign in through the normal parent login and reach the existing family. Use a unique username, email, and strong password.

After recovering normal administration, review active parent accounts and deactivate the emergency account if it is no longer needed. Do not share it, use it for daily family access, or expose Django administration—the Django admin route is disabled by default.
