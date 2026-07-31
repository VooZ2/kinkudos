# Backups

The parent administrator can configure encrypted daily remote copies of the KinKudos database and uploaded family photos. This is strongly recommended once family data matters to you, but it requires a storage provider and careful handling of credentials.

## What is protected

Each successful remote backup includes the family database and uploaded media. KinKudos uses an isolated backup service and encrypted restic snapshots. Storage credentials and the repository password are kept in separately protected server files; they are not stored in the GitHub repository or shown in the parent interface.

Backups do **not** replace a restore plan. Keep the repository password safely outside the server and perform a restore test in a separate, safe location after initial setup.

## Reading the status

| Status | Meaning | First action |
| --- | --- | --- |
| **Enabled** | A remote storage destination is configured and the latest successful copy is no more than seven days old. | Check the date occasionally and keep the repository password safe. |
| **Copying** | A backup is running. | Wait; only one run can run at a time. |
| **Not enabled** | Remote backup storage has not been configured. | Set it up when you have a suitable storage account. |
| **Attention needed** | The backup service is unavailable, no recent successful copy exists, or an error was reported. | Read and record the displayed error before changing anything. |

The panel also shows the provider, repository target, latest successful copy, latest integrity check, and a short audit of recent configuration changes or manual runs.

## Configure storage

Open **Parents → Settings → Backups → Edit settings**. The parent administrator must enter their current parent password. KinKudos verifies the storage connection before saving.

| Field | Meaning |
| --- | --- |
| **Storage provider** | Backblaze B2 through its S3-compatible API, or another S3-compatible provider. |
| **S3 endpoint** | The provider’s S3 API host name, without `https://` or a trailing slash. |
| **Bucket name** | A dedicated storage bucket, without a path. Prefer a bucket used only for KinKudos backups. |
| **Region** | Required by some S3 providers; leave blank only when the provider does not use it. |
| **Application key ID / Application key** | The provider’s limited access credentials. Use a key limited to the backup bucket where possible. |
| **Your account password** | Confirms that the person changing sensitive remote storage is the parent administrator. |

If credentials or the endpoint are wrong, KinKudos does not save the new configuration. Do not repeatedly guess at credentials; use the storage provider’s documentation or ask the server administrator.

## Back up now and restore

**Back up now** requests an additional backup. It does not restore files, overwrite the live database, or bypass the normal encryption and integrity checks.

Restore is deliberately a server-administrator operation. It must be done from the server following the deployment recovery documentation, preferably first in a separate test directory. Never use a live family installation as the first restore test.

[Parent settings →](../parents/settings.md) · [Installation and maintenance →](../deployment-and-maintenance.md) · [Lietuviškai](backups.lt.md)
