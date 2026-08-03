---
title: Restore KinKudos from a backup
description: Prepare a separate KinKudos restore test and understand why live restore steps are withheld until the complete recovery process is release-tested.
---

# Restore KinKudos from a backup

Restore is a server-administrator operation that can destroy newer family data. There is no web restore button and no supported one-command automated restore in this release.

Before any recovery, preserve the current server, identify the exact KinKudos version, secure the restic repository password and required secrets, and make an additional copy of the current `data` directory. Perform the first restore only in an isolated test directory or disposable test VPS.

A restore test is complete only after you have verified:

- the SQLite database passes integrity checks;
- private media exists and opens;
- parent and paired-child access behaves as expected;
- the restored app version and migrations are compatible;
- `app` becomes healthy;
- a new backup can run without overwriting the test source.

Exact live replacement commands are intentionally not published until this complete process has been tested against a released KinKudos archive and remote snapshot. Do not substitute generic restic commands on a production family server.
