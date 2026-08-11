# Network access

Network access is an optional, administrator-only IP allowlist. It adds a layer on top of parent passwords, child PINs, device pairing, and sign-in rate limits; it does not replace any of them.

It is most useful for a stable home network or VPN. It is not a good first step for a family whose home address changes often, or whose parents and children regularly use mobile data away from home.

## Choose the least restrictive mode that solves your need

| Mode | Effect |
| --- | --- |
| **Internet access** | No IP addresses are blocked. This is the normal default. |
| **Restrict child access** | Child pages and shared routes used by an active child session work only from listed IP addresses or networks. Parent pages remain available from other addresses. |
| **Restrict all access** | Both parent and child pages work only from listed addresses or networks. |

With **Restrict child access**, the allowlist also applies when an active child
session uses a shared route such as feedback or screenshot access. It is not
limited to URLs beginning with `/child/`. An authenticated parent is not treated
as a child session for this mode.

## Before saving a rule

1. Check the **Current IP address** shown in the Settings form.
2. Enter one IP address or CIDR network per line. Examples: `192.0.2.25`, `192.0.2.0/24`, or `2001:db8::/64`.
3. If choosing **Restrict all access**, include the current IP before saving. KinKudos refuses to save that mode without it.
4. Keep a server administrator with SSH or console access available until you have tested a parent and child device.

> Do not guess a network range. A wrong all-access rule can lock every parent and child out. The server administrator must then use the documented recovery command to disable network restrictions.

Changing a rule requires the parent administrator’s current password and is recorded as a security event. See [Parent settings](../parents/settings.md) for field-by-field guidance.

[Server administration →](../administration/index.md) · [PINs and sign-in protection →](pin-and-sign-in.md) · [Lietuviškai](network-access.lt.md)
