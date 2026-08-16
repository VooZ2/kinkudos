# Accounts and devices

Every adult should use their own password-protected parent account. Every child has their own profile and PIN, but a child PIN works only on a [paired device](../start/pair-a-child-device.md).

## Parent accounts

Create a separate parent account for each adult who needs to review tasks, approve rewards, or manage family settings. In **Parents → Settings → Accounts**, use **Create account**, choose **Parent account** or **Child profile**, and complete the selected form. Do not share passwords. An email address is important when SMTP password recovery is enabled.

Removing a parent deactivates the account while preserving its history. The last active parent cannot be removed. The first parent created during setup is the parent administrator and controls sensitive settings; another parent may still use all ordinary family features and manage ordinary parent accounts. A normal parent cannot edit or deactivate an administrator account, and the last active administrator cannot be deactivated. Deactivating a parent also removes that account's push subscriptions.

## Child profiles

A child profile stores the child’s name, PIN hash, spendable balance, credit,
individual surprise-card setting, birthday, avatar, theme preference, and
History. Children see only their own private data. The existing-account list
keeps **Parent accounts** and **Child profiles** under separate headings.

Select an edit icon to open an account-edit dialog. **X**, **Cancel**, and
**Escape** close it; **Save** applies the changes. Closing without saving resets
the form and discards unsaved edits. The list and dialogs use a compact layout
on mobile.

Removing a child deactivates the profile and preserves history. It does not erase the child’s point record or transfer it to another child.

## Guest access

Temporary guest access is for grandparents, relatives, or babysitters. In
**Parents → Settings → Guest access**, create an invite, choose which children
the guest may see, and set an access end date. Share the private link from the
dialog (copy, device share sheet, or email when SMTP is enabled). The invite
link is valid for **6 hours** and is consumed when the guest creates a PIN.

Guests sign in with that PIN on a stable guest URL. They can use the family
actions available on Home for their selected children, including reviewing and
deciding ordinary requests and assigning day-to-day tasks, but they cannot open
Manage or Settings, and they do not receive notifications. Parents can unlock a
locked guest PIN or remove guest access at any time. Expired invites and expired
guest access disappear from the settings lists automatically.

## Paired devices

Pairing is the first security gate for children. Until a browser/PWA is paired, it cannot list child names or present the PIN screen. Each device is shown with a broad phone, tablet, computer, or unknown-device classification, a browser summary, a stable six-character ID, and a last-used time. The classification is a convenience label and does not identify an exact model. Unused, unrevoked devices remain visible in the settings list, including after 30 days without use. Name devices clearly, review the last-used time, and revoke a device as soon as it is lost or no longer family-controlled.

An actively used paired device has its access cookie renewed, so an active
pairing should not quietly expire. Revocation removes the device’s child access
and notification subscriptions immediately; the device must be paired again.

The parent administrator can revoke every child device after confirming their
password. That removes child notification subscriptions and requires every
child browser/PWA to be paired again.

[Pair a child device →](../start/pair-a-child-device.md) · [PINs and sign-in protection →](pin-and-sign-in.md) · [Lietuviškai](accounts-and-devices.lt.md)
