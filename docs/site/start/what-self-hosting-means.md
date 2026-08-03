# What self-hosting means

Self-hosting means your family, not KinKudos, operates the server that stores
the application and private family data. This gives your family control, but
also gives it responsibility for the server.

> **For:** The person deciding who will maintain KinKudos<br>
> **Difficulty:** Basic server administration<br>
> **You need:** Linux, Docker, a hostname, HTTPS, and a backup plan

## The family is responsible for

- keeping the server, domain, HTTPS proxy, and Docker installation working;
- protecting server and provider credentials;
- installing the latest KinKudos release;
- configuring and checking backups; and
- deciding who can administer the family and server.

KinKudos keeps application data private to the installation, but it cannot
protect a server that has been left unpatched, publicly exposed by mistake, or
lost without a usable backup.

## What you do not need on day one

SMTP email, remote backups, and network IP restrictions are valuable optional
services, but they are not required before a family can create tasks, pair a
child device, or use points and rewards. Configure them deliberately with the
server administrator instead of blocking the first family setup.

## A practical division of responsibility

| Person | Normal responsibility |
| --- | --- |
| **Parent** | Uses tasks, rewards, approvals, and ordinary family settings. |
| **Parent administrator** | Manages sensitive app settings, paired devices, and family accounts. |
| **Server administrator** | Maintains Docker, HTTPS, updates, storage credentials, backups, and recovery. One person may have all three roles. |

## Next step

If this division is clear, check the [prepared-server requirements](../installation/guided-installer.md)
or start using an installed instance with [your first 15 minutes](first-15-minutes.md).

[Back to Start here →](../index.md) · [Lietuviškai](what-self-hosting-means.lt.md)
