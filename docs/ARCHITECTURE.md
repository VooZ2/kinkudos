# KinKudos — Architecture

## Purpose
KinKudos is a self-hosted, single-family PWA. Children earn points for
approved tasks, can propose rewards or savings goals, and may spend points
down to a per-child negative balance floor.

The codebase is intended to remain publishable on GitHub. Family data,
credentials, secrets, uploaded files, and deployment-specific values stay
outside the repository.

## Stack
Python 3.12 · Django 5.2 LTS · SQLite with WAL · server-rendered templates ·
small vanilla-JavaScript PWA layer · Web Push with VAPID · Gunicorn · one
ARM64/AMD64-compatible application container · an existing external Traefik
reverse proxy.

There is no Node.js toolchain, SPA, or public API. Small internal JSON
endpoints are used where necessary, such as child-state polling for
automatic refresh.

## Accounts
**Parents** — multiple Django `User` accounts managed in the application.
Passwords are hashed with Argon2. Parent sessions last 24 hours
(`KINKUDOS_PARENT_SESSION_SECONDS`). Email-based password reset is optional
and requires SMTP configuration. Removing a parent account deactivates it
(`is_active=False`); it is not physically deleted, and the last active
parent account cannot be removed.

**Children** — multiple `ChildProfile` records managed by parents. Children
sign in with a four-digit PIN hashed with Argon2, never stored raw. Five
failed attempts lock the profile for five minutes; a parent can unlock it
immediately. Child sessions last 48 hours
(`KINKUDOS_CHILD_SESSION_SECONDS`). A device may remember the last selected
child. Removing a child profile deactivates it, same as parent accounts.

A child may access only their own private data and shared catalogs (tasks,
rewards, themes). Cross-child access is forbidden.

## Core data
**FamilySettings** — singleton: family display name, currency name, default
per-child negative balance floor, photo-bonus points, birthday points,
evidence/screenshot retention periods, password-recovery code hash. Not a
source of app versioning or general PWA configuration.

**Task** / **TaskClaim** — shared task catalog, positive point reward. A
child may hold several claims for different tasks at once, but only one
active `pending`/`needs_changes` claim per task.

Lifecycle:
- `pending → approved`
- `pending → rejected`
- `pending → needs_changes → pending` (after resubmission)

Approval and its ledger entry are created in one database transaction.
Optional photo evidence is validated, resized, EXIF-stripped, and retained
per its configured period (`economy/images.py`).

**PenaltyTemplate** — penalty catalog entry storing a negative amount
directly (enforced at the field level). Applying it to a child requires a
reason and immediately creates the corresponding ledger entry.

**Reward** / **RewardRequest** — shared redemption catalog and requests. A
child can cancel their own request while pending. Approval checks the
resulting balance against that child's floor.

**Proposal** — a child proposes a new shared reward or personal savings
goal; a parent approves/rejects and sets the final cost.

**SavingsGoal** — per-child target; progress is calculated against the
child's overall balance, not a separate ring-fenced sub-balance.

**LedgerEntry** — append-only, the single source of truth for balances.
Existing entries can't be modified or deleted; corrections are new
offsetting entries.

**PointGift** — child-to-child transfer with distinct sender and recipient.
Runs inside one atomic transaction: validates the sender has a positive
balance and the amount doesn't exceed it ("only points already earned"),
then creates matching debit/credit ledger entries.

**BirthdayAward** — automatic birthday award, limited to one per child per
calendar year, linked to its ledger entry.

**BirthDateChangeRequest** — child-requested birth-date correction,
parent-approved; one pending request per child at a time.

**PushSubscription** — Web Push subscription for either a parent user or a
child device (exactly one owner, enforced by a DB constraint). Parents are
notified of new/revised task submissions; children are notified of task
and reward decisions, point gifts, and birthday awards.

**FeedbackReport** — in-app bug/idea report from a parent or child, with an
optional screenshot and a review-status workflow.

## Themes
Six built-in themes, all original names/assets, no third-party trademarks:
`neutral`, `magic_academy`, `block_world`, `hero_hq`, `art_studio`,
`panda_pet`. Themes change colors, typography character, illustrative CSS,
icons, and short UI copy.

## PWA
`manifest.webmanifest`, dedicated icons, `display: standalone`. The service
worker caches only static assets and the offline fallback page — balances
and pending requests are never cached long-term. Push subscriptions
available to both parent and child sessions. iOS requires the app to be
added to the home screen for Web Push to work.

## Security
- Traefik `ipAllowList` via `KINKUDOS_ALLOWED_NETWORKS`; TLS via the
  existing `letsencrypt` resolver with `tlsChallenge`.
- Django `SECURE_PROXY_SSL_HEADER`; `HttpOnly`, `SameSite=Lax` cookies.
- CSRF protection on all mutating requests. No CORS — same-origin only.
- Every parent/child request is authorized server-side.
- Balance-changing operations use `transaction.atomic()` with row locking.
- Secrets are read only from Docker secret files or server environment
  variables — no default passwords/PINs/family data ship in the image.
- Automatic Watchtower updates are disabled.

## Deployment layout
```text
kinkudos/
├── app/       # publishable application code
├── deploy/    # shared Compose + Traefik config, no secrets
├── data/      # SQLite + uploaded media
├── backups/   # local backup copies
└── secrets/   # Django, VAPID, SMTP, backup secrets
```
The deployment service account may modify only `app` and `deploy`; runtime
data, backups, and secrets remain separately permissioned.

## Backups
SQLite online-backup mechanism; local copies kept 31 days; encrypted
`restic` copy to any restic-compatible repository, using credentials scoped
to that repository. A backup configuration is not considered complete
until a restore test has been performed successfully. Whole-server backup
planning is a separate operational concern.

## Versioning
MIT license, semantic versioning, `main` must always pass its test suite.
Current released version: the latest versioned entry in `CHANGELOG.md`
(entries under `[Unreleased]` are not yet released). Family data is
created at install time, never shipped in the repo.

## Deliberately out of scope (for now)
Recurring tasks · achievements/badges · levels/streaks/leaderboards ·
Telegram integration · CSV/Excel export · multi-family hosting in one
instance. This is a scope note, not a version plan — update it when any
item ships.
