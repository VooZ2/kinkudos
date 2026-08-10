# Roles, data, and limits reference

Use this reference when you need a short factual answer rather than a guided
workflow.

## Where family data lives

| Data | Location and handling |
| --- | --- |
| Family settings, accounts, profiles, points, and history | KinKudos database on the family server. |
| Task evidence, avatars, and feedback screenshots | Private uploaded media on the family server. |
| Savings goals and goal events | Goal records and event history in the family database; separately saved allocations are linked to their specific goal. |
| Secrets and provider credentials | Separately protected server files; never shown in the public repository. |
| Optional remote backups | Encrypted restic snapshots of the database and uploaded media. |

KinKudos has no ads or built-in analytics in the private family application.
The public documentation has separate cookie-free analytics only.

## Important limits and time rules

| Rule | Value or behavior |
| --- | --- |
| Child-device pairing link | Single use; expires after 10 minutes. |
| Paired-device profile | Broad phone, tablet, computer, or unknown-device classification; short stable six-character ID; browser summary; and last-used time. The list marks a device **Not used recently** after 30 days. |
| Active paired-device access | The access cookie is renewed while the device is actively used. Revoking the device invalidates child access and notifications immediately. |
| Child PIN | Four digits; a child profile needs a paired device first. |
| Task/feedback image upload | JPEG, PNG, WebP, HEIC, or HEIF up to 12 MB. |
| Avatar upload | The same formats up to 5 MB; cropped to a square. |
| Assigned task deadline | Midnight in the server’s local time. |
| Scratch-ticket week | Monday through Sunday. |
| Completed task-photo retention | Family choice: indefinitely, 7, 30, or 90 days. |
| Resolved-feedback image retention | Family choice: indefinitely, 7, 30, or 90 days. |

## Points and savings-goal accounting

`LedgerEntry` remains the source of truth for spendable points. Separately
saved goal allocations are not spendable. Moving points into a separately
saved goal creates a negative ledger entry; returning them creates a positive
spendable ledger entry. Selecting or switching a **Current goal** changes no
ledger balance. Separately saved goal completion consumes the saved allocation
without deducting the points again, while available-points completion deducts
the target once after parent approval.

## Related policies

- [Release and support policy](release-and-support-policy.md)
- [Security policy on GitHub](https://github.com/VooZ2/kinkudos/security/policy)

[Lietuviškai](roles-and-data.lt.md)
