---
title: KinKudos first-time web setup
description: Use the one-time setup code to create the family, first parent administrator, language, timezone, recovery code, and optional SMTP settings.
---

# First-time web setup

After the server starts, open the HTTPS address printed by the installer, ending in `/setup/`. An unfinished installation redirects ordinary application pages to this setup route.

!!! danger "Protect the unfinished installation"
    Complete setup promptly, use HTTPS, and do not share the setup code. Anyone who has network access to the new installation and knows this code may attempt to create the first parent administrator.

## Complete the form

Enter:

| Field | What to use |
|---|---|
| **Setup code** | The high-entropy code printed by the server installer. |
| **Parent username** | A memorable, unique sign-in name for the first adult. |
| **Email address** | A valid address. It is used for email password recovery after SMTP is enabled. |
| **Password** | A strong, unique password that passes the displayed validation rules. |
| **Family name** | A private family name or nickname shown inside this installation. |
| **Default language** | English or Lithuanian. Individual devices can switch later. |
| **Timezone** | The family’s real timezone, used for dates and scheduled work. |

### Optional email configuration

Select **Configure email now** only when you already have correct SMTP details. KinKudos works without SMTP. Without it, email password recovery and optional feedback notification emails are unavailable.

If selected, provide the SMTP host, port, security mode, username, password, sender address, and feedback recipient address. KinKudos verifies the SMTP connection before completing the form. See [SMTP configuration](../administration/smtp.md) for each field.

## Save the recovery code

After successful setup, KinKudos signs you in and shows the recovery code once. Save it in a password manager before leaving the page. It is not shown again, remains valid until it is rotated, and is required by the KinKudos CLI recovery command.

Setup then becomes permanently unavailable. Revisiting `/setup/` sends a signed-in parent to the dashboard or a signed-out visitor to parent sign-in.

## If setup is interrupted

If the form reports an error, correct it and submit again. The parent account, family, and completed marker are created atomically, so a validation or SMTP connection failure does not leave a partial family account.

If the setup page no longer appears, do not try to bypass its lock. Check [Setup page problems](../troubleshooting.md#setup-page-does-not-appear) or use the documented [password recovery](../administration/password-recovery.md) route for an existing installation.
