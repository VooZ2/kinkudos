# Parent settings

Path: **Parents → Settings**. The page is organised into the same groups as
the application. On a phone, groups are compact expandable sections: selecting
one reveals its fields, and empty sections are not shown. The **Accounts**
section has one account-creation panel and one list of existing accounts; its
edit forms open in dialogs that also fit small screens.

> **Who can change what?** Every parent can use ordinary family settings and
> manage ordinary parent accounts and child profiles. A normal parent cannot
> edit or deactivate a parent administrator. The parent administrator is the
> only person who can manage an administrator account or change network access,
> SMTP, backup credentials, run a backup, or revoke every child device.

<img class="screenshot-image" src="../../assets/parent-settings-devices-26-6-4.png" alt="Parent settings with paired devices" loading="lazy">

<details class="screenshot-disclosure" open>
<summary><span class="screenshot-disclosure__icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M5 4h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2m0 2v12h14V6zm2 10 2.8-3.5 2 2.4 2.7-3.4L18 16zM16.5 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3"/></svg></span><span class="screenshot-disclosure__label">View paired devices on mobile</span><span class="screenshot-disclosure__arrow" aria-hidden="true"></span></summary>
<img class="screenshot-image" src="../../assets/parent-settings-devices-mobile-26-6-4.png" alt="Paired devices in parent settings on mobile" loading="lazy">
</details>

<details class="screenshot-disclosure" open>
<summary><span class="screenshot-disclosure__icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M5 4h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2m0 2v12h14V6zm2 10 2.8-3.5 2 2.4 2.7-3.4L18 16zM16.5 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3"/></svg></span><span class="screenshot-disclosure__label">View Accounts on desktop and mobile</span><span class="screenshot-disclosure__arrow" aria-hidden="true"></span></summary>
<img class="screenshot-image" src="../../assets/parent-settings-accounts-26-6-4.png" alt="Accounts in parent settings on desktop" loading="lazy">
<img class="screenshot-image" src="../../assets/parent-settings-accounts-mobile-26-6-4.png" alt="Accounts in parent settings on mobile" loading="lazy">
</details>

<details class="screenshot-disclosure" open>
<summary><span class="screenshot-disclosure__icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M5 4h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2m0 2v12h14V6zm2 10 2.8-3.5 2 2.4 2.7-3.4L18 16zM16.5 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3"/></svg></span><span class="screenshot-disclosure__label">View the account edit dialog</span><span class="screenshot-disclosure__arrow" aria-hidden="true"></span></summary>
<img class="screenshot-image" src="../../assets/parent-settings-account-edit-26-6-4.png" alt="Child profile edit dialog in parent settings" loading="lazy">
<img class="screenshot-image" src="../../assets/parent-settings-account-edit-mobile-26-6-4.png" alt="Child profile edit dialog on mobile" loading="lazy">
</details>

The screenshots use fictional demonstration data.

## Family

### Family name

The **Family name** appears in family-facing headings and messages. It changes
the displayed name only; it does not change account names, domain names, or
access.

## Points and tasks

These values affect future activity and do not rewrite completed work or
existing History entries.

| Field | What it means |
| --- | --- |
| **Points for a task photo** | Extra points awarded when a child submits a task with a photo. Use `0` to turn the bonus off. The value is captured when the task is submitted. |
| **Birthday points** | A yearly gift awarded once for each child’s saved birthday. Use `0` to disable it. The same child is not awarded twice in one calendar year. |

## Scratch tickets

These family-wide controls work together with the individual switch in
**Parents → Settings → Accounts**, under **Child profiles**:

| Field | What it means |
| --- | --- |
| **Enable scratch tickets** | Master switch. Turning it off prevents new purchases and reminders, but an already-open ticket can still be finished. |
| **Scratch ticket price** | The point cost for future tickets. A ticket already bought keeps its recorded cost. |
| **Weekly ticket limit** | How many tickets one child may buy from Monday through Sunday. The count resets every Monday. |

Scratch tickets are optional; they are not required for ordinary tasks or
rewards.

## Data and retention

These fields control automatic deletion of uploaded images, not account
history or point records.

| Field | What it means |
| --- | --- |
| **Keep task photos for** | Completed task-photo retention: indefinitely, 7, 30, or 90 days. Pending or revision-requested photos are not removed automatically. |
| **Keep feedback images for** | Retention for a screenshot attached to a resolved feedback report. Unresolved feedback screenshots are not removed automatically. |

## Children and access

### Child devices

Only a paired device can list child profiles or accept a child PIN. A profile
stores the child’s rules and history; a device is the browser, phone, tablet,
or PWA allowed to use that profile. KinKudos classifies a paired device broadly
as a phone, tablet, computer, or unknown device from its browser information.
This is a convenience label, not an exact model or fingerprint.

| Control | Result |
| --- | --- |
| **Device name** | Optional label for the device, for example “Kitchen tablet”. If left blank, KinKudos uses the detected device summary after pairing. |
| **Allow on this device** | Pairs the current browser/PWA immediately. It can then select a child and accept a PIN. |
| **Send a link** | Creates a single-use private link that expires after **10 minutes**. Open it only on the intended device. |
| **Device summary** | Shows a broad icon and description such as **iPhone · Safari**, **Android phone · Chrome**, **iPad · Safari**, **Android tablet · Chrome**, **Mac**, **Windows PC**, or **Linux PC**. Unknown devices remain labelled as unknown. |
| **ID** | Shows a short, stable six-character identifier so a parent can distinguish entries. It is not a pairing credential. |
| **Last used** | Shows when the device was last active. After 30 days without use, the list also shows **Not used recently**. |
| **Rename** | Opens an inline form for changing the device label without interrupting access. |
| **Revoke** | Removes child access and notifications from one lost or retired device. On mobile, this is shown as a compact trash-can icon. The device must be paired again before sign-in. |
| **Revoke all child devices** | Administrator-only. Requires the administrator’s password and forces every child browser/PWA to pair again. |

Read [Pair a child device](../start/pair-a-child-device.md) before using a
private link. When a paired device is actively used, its access cookie is
renewed so an active pairing should not quietly expire. Revoking the device
still invalidates it immediately; it must be paired again.

### Network and security

Network access is an optional extra security layer. Parent passwords, child
PINs, and device pairing remain active when IP restrictions are disabled.

| Mode | What it allows |
| --- | --- |
| **Internet access** | No IP restriction. |
| **Restrict child access** | Only listed IP addresses or networks can use child pages; parent pages are not restricted by IP. |
| **Restrict all access** | Only listed IP addresses or networks can use child and parent pages. |

For **Allowed IP addresses and networks**, enter one IPv4 address, IPv6
address, or CIDR network per line, such as `192.0.2.25`, `192.0.2.0/24`, or
`2001:db8::/64`. Before choosing **Restrict all access**, include the current IP
shown on the page. A wrong rule can lock everyone out and requires server
administrator recovery.

In **Restrict child access** mode, parent login and password-recovery pages
remain available even when the browser has an active child session. A parent can
therefore authenticate or recover the account from that device. After
authentication, the request is evaluated as parent access; child-only and pairing
flows remain restricted as child routes.

## Email and notifications

SMTP is optional. It is used for parent password-recovery messages and, when a
feedback recipient is configured, notifications about private in-app feedback.
The report remains stored in KinKudos when email is disabled. Browser or PWA
notifications are enabled from the notification control on the signed-in
screen; on iPhone and iPad, install KinKudos to the Home Screen first.

The page shows the SMTP server, sender address, and feedback recipient when
email is enabled, but never the SMTP password. **Edit settings** requires the
administrator’s current parent password, and the SMTP password must be
entered again whenever sensitive settings are saved.

| Field | What to enter |
| --- | --- |
| **Enable email** | Turn email delivery on or off. |
| **SMTP server** | The provider’s outgoing-mail host, such as `smtp.example.com`. |
| **SMTP port** | The provider’s port, commonly 587 for STARTTLS or 465 for SSL/TLS. |
| **Encryption** | `STARTTLS`, `SSL/TLS`, or `None`; use `None` only for a trusted private relay. |
| **SMTP username** | The mail service login. |
| **SMTP password** | The mail-service or app password; it is never displayed after saving. |
| **Sender email address** | The address recipients see as the sender. |
| **Feedback recipient email address** | Where optional feedback notifications are sent. |
| **Your account password** | The administrator’s current password, required to protect sensitive changes. |

## Backups

The backup service makes encrypted daily remote copies of the family database
and uploaded photos. Restoring is a server-administrator operation, not a web
button.

The status can be **Enabled**, **Copying**, **Not enabled**, or **Attention
needed**. The panel also shows the provider, repository, **Last successful
backup**, **Last integrity check**, errors, and recent backup actions.

A scheduled failure is not recorded as that day's success. The backup service
may retry later on the same day with bounded backoff; after a scheduled run
succeeds, it does not repeat that day's backup.

**Back up now** requests an additional copy; it never restores data and does
not run while another backup is in progress. Before changing credentials, keep
the repository password outside the server and plan a restore test.

| Field | What to enter |
| --- | --- |
| **Storage provider** | `Backblaze B2 (recommended)` or another S3-compatible provider. |
| **S3 endpoint** | The provider’s S3 API host without `https://` or a trailing slash. |
| **Bucket name** | A dedicated bucket for KinKudos backups. |
| **Region** | The provider’s region when required. |
| **Application key ID / Application key** | Access credentials limited to this backup bucket when possible. |
| **Your account password** | The current administrator password. |

KinKudos verifies the connection before saving. Provider credentials are kept
outside the database in separately protected server files. A green status is
not a substitute for a restore test.

## Accounts

The **Accounts** section has two panels:

1. **Create account**: choose **Parent account** or **Child profile** from
   **Account type**. Only the form for the selected type is shown. In the
   Lithuanian interface, the choices are **Tėvų paskyra** and **Vaiko
   profilis**.
2. **Existing accounts**: one list with separate **Parent accounts** and
   **Child profiles** headings.

Create a separate parent account for each adult with a username, email address,
and strong password. Create a child profile with the child’s name, optional
Lithuanian greeting form, starting PIN, credit, individual scratch-ticket
switch, and birthday. The child chooses a theme on first sign-in.

Select the edit icon beside an existing account to open its edit dialog. Close
the dialog with **X**, **Cancel**, or **Escape**, or choose **Save** to keep the
changes. Closing it without saving resets the form and discards unsaved edits.
On mobile, the account list and dialog are arranged for a narrow screen.

Leaving new-password fields empty keeps the existing password. Removing a
parent deactivates the account and preserves its History. Only the parent
administrator can edit or deactivate an administrator account. The final active
parent cannot be removed, and the final active parent administrator cannot be
deactivated. Deactivating a parent also removes that account's push
subscriptions.

| Field | What it changes |
| --- | --- |
| **Child’s name** | The displayed name; names must be unique. |
| **Vocative name** | An optional Lithuanian greeting form. |
| **Credit** | The child’s lowest permitted balance, such as `-100`; it is the same rule shown on the child card. |
| **Enable scratch tickets for this child** | Individual permission; the family-wide switch must also be on. |
| **Birthday** | The yearly birthday-points rule. Parents can edit it directly; a child’s requested change needs approval. |
| **New PIN / Repeat new PIN** | Resets the child’s four-digit PIN. Leave both blank to keep it unchanged. |

Removing a child deactivates the profile and preserves its History. It does not
transfer that child’s data to another child.

## Family feedback

Parents and children can submit a private **idea** or **problem** report from
the app. The report stays on this server. If SMTP feedback notifications are
configured, KinKudos can also email the chosen recipient.

Use the **Type** and **Status** filters. **New** means not reviewed; **Reviewed**
means a parent has read it; **Planned** means the family intends to act; and
**Resolved** means no further action is expected. Open a report to read its
description, view its optional screenshot, and save its status.

KinKudos records the reporting role and name, page path, app version, language,
selected theme, and browser/device description. This remains in the family
installation and is not sent to GitHub. Feedback screenshots follow the
retention rule above.

## Image limits and time rules

Task photos and feedback screenshots accept JPEG, PNG, WebP, HEIC, or HEIF up to
**12 MB**. Avatars use the same formats up to **5 MB** and are cropped to a
square.

Daily assigned tasks expire at midnight in the **server’s local time**.
Scratch-ticket limits reset every Monday in that same calendar context.

[Network access →](../security/network-access.md) · [Backups →](../backups.md) · [Family administration →](../family-administration.md) · [Lietuviškai](settings.lt.md)
