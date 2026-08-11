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
published ARM64/AMD64 application image · a supported Nginx, Traefik, or
container-based TLS reverse proxy.

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
The first parent is created in the browser-only initial setup and is the parent
administrator (`is_staff=True`). The installer generates a high-entropy setup
code, stored as a local secret, so a person who merely reaches a fresh public
hostname cannot claim the first account. Setup creates the first parent and
family settings atomically; after it succeeds, server-side checks permanently
disable it. Ordinary parents can manage ordinary parent accounts, but cannot
edit or deactivate an administrator. The last active administrator cannot be
deactivated. Deactivating any parent also removes that parent's push
subscriptions. All parents may see backup health, but only the parent
administrator may change backup credentials or request a manual backup.

**Children** — multiple `ChildProfile` records managed by parents. Before a
device can see child names or submit a PIN, a parent pairs it with a
high-entropy, revocable `DeviceToken`. Children then sign in with a four-digit
PIN hashed with Argon2, never stored raw. Device, profile, IP, and site-wide
attempt limits protect the PIN flow; five failed profile attempts also lock
the profile for five minutes, and a parent can unlock it immediately. Child
sessions are bound to the paired device and last 48 hours
(`KINKUDOS_CHILD_SESSION_SECONDS`). A device may remember the last selected
child. Removing a child profile deactivates it, same as parent accounts.

A child may access only their own private data and shared catalogs (tasks,
rewards, themes). Cross-child access is forbidden.

## Core data
**FamilySettings** — singleton: family display name, currency name, default
per-child negative balance floor, photo-bonus points, birthday points,
family-wide lottery availability, ticket price and weekly purchase limit,
evidence/screenshot retention periods, optional application-level network
access mode and allowed IPv4/IPv6 CIDRs, password-recovery code hash, initial
setup completion state, default interface language, and family timezone. The
timezone is activated for requests and lottery reminders so daily/weekly rules
follow the household clock. Not a source of app versioning or general PWA
configuration.

**DeviceToken** / **DevicePairingLink** — a paired child browser/PWA and its
short-lived, single-use bootstrap link. Only SHA-256 token digests are stored.
Each pairing also receives a broad, non-fingerprinting device profile and a
short public identifier for parent-side recognition. Child sessions and child
Web Push subscriptions are bound to a non-revoked device. Active device cookies
are renewed while the device is used, while revocation removes that device's
child push subscriptions immediately.

**AttemptCounter** — shared fixed-window authentication counters stored in
SQLite so limits remain consistent across Gunicorn workers. Keys are HMAC
digests of IP, account, profile, or device dimensions and old rows are removed
by daily maintenance.

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

**AssignedTaskBatch** / **AssignedTask** / **TaskCompletion** — a parent may
send one child a list of catalog tasks plus one optional custom task for the
current calendar day. The batch stores the assigning parent, assignment date,
and whether new reward requests are blocked while any item is waiting. Each
item snapshots its title, icon, and point value so later catalog edits do not
change work that was already sent.

Assigned items have `pending`, `completed`, or `cancelled` status. A child
completes each item separately and receives its points immediately in the
same database transaction that closes the item and creates its
`assigned_task` ledger entry. Catalog-backed completion also creates a
`TaskCompletion` record for that child and calendar day. This prevents a
catalog task from being assigned while it awaits approval, is already
assigned, or has already been credited that day. Cancelled items can be
assigned again; completed catalog tasks become available on the next day.

Pending items are active only when `AssignedTaskBatch.assigned_on` equals the
server-local calendar date. At midnight they disappear from the child's
priority list, stop blocking new reward requests, and remain visible as
expired in parent history. Blocking applies only to new reward purchases:
existing pending reward requests can still be approved or rejected, and all
other child actions remain available.

**PenaltyTemplate** — penalty catalog entry storing a negative amount
directly (enforced at the field level). Applying it to a child requires a
reason and immediately creates the corresponding ledger entry.

**Reward** / **RewardRequest** — shared redemption catalog and requests. A
child can cancel their own request while pending. Approval checks the
resulting balance against that child's floor.

**LotteryTicket** — built-in system reward with a family-configurable purchase
price and per-child Monday–Sunday purchase limit. A family-wide master switch
has priority over the per-child availability switch. Disabling the lottery
blocks new purchases and reminders, while an already-open ticket remains
available to finish. A purchase atomically deducts the configured number of
earned points and stores a server-generated 3×3 board with a preselected
positive, negative, or no-prize result. Only one ticket may remain open per
child, and a negative reveal is clamped to the child's balance floor. Purchase
and reveal use separate append-only ledger entries. The standard 50/30/20
outcome draw is overridden only by the per-child jackpot guarantee after
eleven tickets without a +101…+150 result.

**LotteryReminder** — per-child weekly schedule and delivery audit for the
optional Web Push reminder. A dedicated idempotent management command checks
due reminders every 30 minutes. It sends at most once in the second half of a
week, only when the lottery is available to that child, the subscribed child
has at least 50 points and enough for the configured ticket price, has bought
no ticket that week, and is not blocked from rewards.

**Proposal** — a child proposes a new shared reward or personal savings
goal; a parent approves/rejects and sets the final cost.

**SavingsGoal** — per-child target with one of two explicit modes. An
`available` goal tracks the child's current non-negative spendable balance;
only one active goal per child may use that mode. A `saved` goal uses
ring-fenced points represented by append-only **SavingsContribution** rows.
Saving points deducts them from the spendable ledger, while returning points
creates an offsetting ledger entry and resolves the active contributions.

**GoalCompletionRequest** — a child request created after a savings goal
reaches its target. A parent must approve completion or keep the goal active;
there can be only one pending request per goal. **SavingsGoalEvent** preserves
the goal activity history independently of the goal's active, completed, or
cancelled state.

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
paired child device (exactly one owner, enforced by a DB constraint). Browser
endpoints must be public HTTPS URLs with bounded, structurally valid Web Push
keys; subscription counts are bounded per parent and child device. Parent
queries include only active users. Parents are notified of new/revised task
submissions, reward requests, suggestions, and birthday-change requests;
children are notified of task, reward, suggestion, and birthday-change
decisions, newly assigned daily work, point gifts, and birthday awards.

**FeedbackReport** — in-app bug/idea report from a parent or child, with an
optional screenshot and a review-status workflow.

## Themes
Seven built-in themes using KinKudos-authored CSS and no third-party logos or
assets:
`neutral`, `magic_academy`, `block_world`, `hero_hq`, `art_studio`,
`panda_pet`, `blockville`. Themes change colors, typography character,
illustrative CSS, icons, currency forms, sounds, and short UI copy. All theme
names, currencies, and copy are KinKudos-authored and avoid third-party marks.

## PWA
`manifest.webmanifest`, dedicated icons, `display: standalone`. The service
worker handles Web Push and may send `kinkudos-state-changed` messages to open
clients as a fast refresh signal, but it does not intercept normal HTML
document navigation. Lightweight Parent workspace and Child session state
polling runs where configured and remains the reliable refresh fallback. Push
subscriptions are available to both parent and child sessions. iOS requires
the app to be added to the home screen for Web Push to work.

Application URL paths are canonical, lowercase English paths using kebab-case
where needed and do not change with the selected interface language. Named URL
reversing is the source for application links, polling, Push payloads, and
emails. Changed public GET paths retain permanent redirects from their previous
Lithuanian paths; legacy mutating paths call the same view so the HTTP method
and request body remain intact. Legacy redirect query strings are rebuilt from
a small allowlist; `next` is retained only as a validated internal relative URL,
and unknown or unsafe values are discarded.

The systemd deployment installs a daily maintenance timer and a separate
30-minute lottery-reminder timer. Generic deployments must schedule the
corresponding Django commands themselves.

## Parent interface palette
The shared parent, landing, and system interface uses a fixed semantic palette:
charcoal `#1F2937` for primary text, headings, and icons; muted gray `#6B7280`
for explanations, dates, inactive controls, and footer text; off-white
`#F9FAFB` for the background; warm plum `#4C1D95` for primary actions and
navigation; sage green `#10B981` for success; amber `#F59E0B` for attention
and pending states; and soft red `#EF4444` for errors, penalties, negative
balances, rejected work, and destructive actions. Pure black is not part of
the shared parent palette.

## Security
- TLS terminates at the operator's supported reverse proxy; Gunicorn is never
  published directly to the internet.
- Forwarded client IP and scheme headers are honored only from configured
  trusted proxy networks. Authentication limits use the resolved address.
- Parent login, password recovery, device pairing, child PIN, and optional
  Django admin endpoints have shared database-backed attempt limits.
- Child profiles are hidden until a parent pairs the device. Pairing links are
  single-use, expire after ten minutes, and pass their secret in the URL
  fragment so it is not written to normal HTTP access logs.
- An optional Django-level IPv4/IPv6 allowlist can restrict child routes or
  the whole application independently of the chosen proxy. In child-only
  mode, an active child session is restricted even on shared routes such as
  feedback and screenshot access, while parent login and password-recovery
  routes remain available so a parent can authenticate or recover the account
  from that device. After authentication, the parent session is evaluated
  before child-session restrictions. Child selection and pairing routes remain
  explicitly restricted. A server-side management command provides recovery
  from an accidental lockout.
- Django admin is disabled in production unless explicitly enabled.
- Django `SECURE_PROXY_SSL_HEADER`; `HttpOnly`, `SameSite=Lax` cookies.
- CSRF protection on all mutating requests. No CORS — same-origin only.
- `DEBUG` defaults to `False`; production requires an explicit secret key.
  Application responses include a nonce-based Content Security Policy that
  restricts scripts, forms, frames, workers, and plugins to the application
  origin; local image previews and existing inline styles remain supported.
- Every parent/child request is authorized server-side.
- Balance-changing operations use `transaction.atomic()` with row locking.
  Proposal, reward-approval, reward-rejection, and reward-cancellation state
  changes also claim `pending` rows with conditional updates, so SQLite does
  not depend on `select_for_update()` alone for one-winner transitions.
- Secrets are read only from Docker secret files or server environment
  variables — no default passwords/PINs/family data ship in the image.
- Automatic Watchtower updates are disabled.

## Deployment layout
```text
kinkudos/
├── app/       # optional checked-out application source
├── deploy/    # shared Compose + selected proxy overlay, no secrets
├── data/      # SQLite + uploaded media
├── backups/   # local backup copies
├── backup-state/ # sanitized backup health state
└── secrets/   # Django, VAPID, SMTP, backup secrets
```
The deployment service account may modify only `app` and `deploy`; runtime
data, backups, and secrets remain separately permissioned.

Fresh installations may start with the small public `deploy/install.sh`
bootstrapper. It resolves a published release, downloads the release archive
and its SHA256 file, verifies the checksum, refuses a non-empty installation
root, and then hands control to the versioned interactive `bootstrap.sh`.
Production Compose files pin the full release tag from the public
`vooz2/kinkudos` Docker Hub repository; `latest` and partial-version tags are
published for discovery but are not used by supported deployments.
The application joins an internal app↔backup network and a separate non-
internal app-egress network. The backup agent keeps its internal app network
separate from its own outbound network; neither service publishes a backup
port. The installer prepares secrets, verifies and starts the containers, then prints
the application URL and setup code; it never collects family account details
or PINs in the terminal. SMTP remains optional and can be skipped during
browser setup or configured later by the parent administrator.

The Hostinger Docker Manager Catalog profile is a separate deployment contract
defined by `deploy/hostinger/compose.yaml`. It runs only the application
container and lets Hostinger's existing host-network Traefik instance terminate
TLS and route the configured hostname to Gunicorn on container port 8000.
Traefik discovery uses Docker labels; the application publishes no host port,
joins no guessed external proxy network, and receives no Docker socket access.

All Hostinger Catalog runtime state is stored in one named volume mounted at
`/app/data`: SQLite, private uploaded media, and generated runtime secrets.
On first start the application entrypoint creates the Django secret and VAPID
key pair with owner-only permissions. Container restart, Compose recreation,
Docker Manager update, VPS restart, and whole-VPS snapshot restore must retain
that volume and must not regenerate the secrets. The Catalog Compose does not
include the backup agent, configure or use Restic, or require backup secrets.

Hostinger automatic whole-VPS backups and a manually created snapshot before
an update are the tested Catalog MVP recovery path. They restore the complete
VPS and overwrite its current state; they are not a portable application-level
KinKudos backup. Application export and portable backup/restore remain separate
future functionality. Discovery and application of updated Catalog Compose
templates or image tags without terminal access remains dependent on a defined
Hostinger Docker Manager update workflow and must not be represented as
automatic, one-click, or suitable for non-technical operators until verified.

## Backups
An isolated `backup-agent` container owns the remote-storage credentials and
has no published port or Docker socket. The application reaches it only over
an internal Compose network authenticated with a generated service token.
The application never receives stored provider secrets back from the agent.
This backup-agent architecture applies to the standard Compose deployment; the
Hostinger Docker Manager Catalog profile intentionally does not include it.

The agent creates a consistent SQLite online backup, includes private uploaded
media, keeps local database copies for 31 days, and sends encrypted snapshots
through `restic`. Backblaze B2 through its S3-compatible API and generic
S3-compatible storage are configurable in the parent UI. Existing
provider-neutral `restic.env` repositories remain usable after an upgrade.
Only provider, repository target, timestamps, health, and masked key metadata
are exposed to parents.

Backups run once daily after the configured hour and can be requested manually
by a parent administrator. Only one run can execute at a time. A scheduled
attempt is successful only after the remote upload, retention/prune operation,
and `restic check` all succeed; the scheduled date is recorded only then.
Temporary failures retry later on the same day with bounded exponential
backoff, rather than retrying every scheduler minute. Green health means the
latest successful remote copy is no older than seven days; an error is shown
separately.

Provider credentials, the `restic` repository password, and agent token remain
in separately permissioned files under `secrets/`. Configuration changes and
manual requests are audited without secret values. Restore remains an explicit
server-administrator operation and is never exposed as a web action. A backup
configuration is not considered complete until a restore test has succeeded.
Whole-server backup planning and an offline copy of the repository password
remain operator responsibilities.

SMTP settings are editable only by the parent administrator after password
confirmation. The SMTP password is stored in a separately permissioned local
file under `secrets/`, never in the database, logs, or repository.

## Versioning
MIT license, calendar-based `YY.FEATURE.FIX` versioning, and `main` must always
pass its test suite. `YY` is the release year's final two digits, `FEATURE`
increments for new functionality, and `FIX` increments for bug fixes, design
changes, and extensions of existing functionality.
Current released version: the latest versioned entry in `CHANGELOG.md`
(entries under `[Unreleased]` are not yet released). Family data is
created at install time, never shipped in the repo.

## Deliberately out of scope (for now)
Recurring tasks · achievements/badges · levels/streaks/leaderboards ·
Telegram integration · CSV/Excel export · multi-family hosting in one
instance. This is a scope note, not a version plan — update it when any
item ships.
