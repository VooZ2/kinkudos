# Project Context

## Status
KinKudos is a production self-hosted application used daily by one family.
It is not a prototype: changes must remain conservative and backward-compatible
because installations contain real family data.

Check `CHANGELOG.md` for the current released version and
`docs/TODO.lt.md` for current open work.

## Stack
Django 5.2, SQLite, Whitenoise, one web application container and one isolated
backup-agent container. Server-rendered
templates, with small internal JSON endpoints where needed (e.g. child
balance polling) — no separate public API, SPA, Node.js, or frontend
framework. Single-tenant: one deployment = one family, no multi-tenancy
code paths exist or are needed.

## Core domain
- `ChildProfile` — child accounts, PIN-based session login
- `Task` / `TaskClaim` — chores lifecycle:
  submit → approve / reject / return for revision → optional resubmit
  (no child-side cancel for tasks)
- `Reward` / `RewardRequest` — point redemption; child can cancel while pending
- `Proposal`, `SavingsGoal`, `PointGift`, `BirthdayAward`, `PenaltyTemplate` — secondary economy mechanics
- `LedgerEntry` — single source of truth for point balances

## Domain invariants
- Never award, deduct, or transfer points outside the ledger flow.
- Balance-changing operations must remain atomic.
- Ledger entries are append-only: never edited or deleted; corrections use new entries.
- A child must never access another child's private data or actions.
- English and Lithuanian user-facing behavior must remain equivalent.
- Existing installations must remain upgradeable without losing family data.
- Family data, secrets, databases, backups, and uploaded files must stay out of Git.

## Working style
- Maintained by one primary contributor using Codex.
- Immediate focus: UI/design polish and EN/LT text fixes. New features are
  still added as they come up, just not the current priority.
- Backlog grows organically from family usage/feedback, tracked in
  `docs/TODO.lt.md` — no separate long-range roadmap.
- `economy/views.py` is large (~1800 lines) but functional; not an active
  refactoring target.

## Repository intent
The repository is intended to be safe for public access. Keep secrets, family
data, and deployment-specific values out of Git.

## Test status
The full `economy` test suite is expected to pass on `main`.
- Run the narrowest relevant tests during day-to-day development.
- Run the full suite before completing any substantial or cross-cutting change.
- Always run the full suite and `scripts/verify_release.py` before a release.
If the full suite fails on a fresh checkout of `main`, treat it as a bug,
not as the new baseline.
