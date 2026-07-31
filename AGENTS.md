# AGENTS.md

## Project

KinKudos is a self-hosted Django PWA for one family.
The public repository must never contain family data, credentials,
deployment-specific secrets, database files, or uploaded images.

## Read before working

Read only the documents relevant to the task:

- Product and development overview: `README.md`
- Architecture and security constraints: `docs/ARCHITECTURE.md`
- Current project state: `docs/PROJECT_CONTEXT.md`
- Release rules: `docs/RELEASING.md`
- Pending work: `docs/TODO.lt.md`
- User-visible changes: `CHANGELOG.md` and `CHANGELOG.lt.md`

## Working rules

- Check git status first. Do only the requested task, no unrelated refactors.
- No new dependencies unless required. No deploy/DB/auth/permissions/ledger/backup logic changes unless the task needs it.
- Never commit .env, secrets, data/kinkudos.sqlite3, backups, uploads, PINs, family data.
- Never access production or run deploy/restore/destructive DB/data-deletion commands unless explicitly requested.
- Keep EN/LT user-facing text and behavior in sync.
- Add/update tests for changed behavior. Never weaken, delete, or rewrite existing tests just to make a failing implementation pass — only when the requested behavior intentionally changed.
- Dev: run only the narrowest relevant test module/class (python manage.py test economy.tests.<module>), not the full suite.
- When translation source files change: python scripts/compile_translations.py.
- ruff check . before finishing; fix warnings you introduced.
- Pre-release only: python manage.py test economy + python scripts/verify_release.py.
- Update both changelogs for user-visible changes. No version bump for docs-only changes.
- No release/deploy/subagents unless explicitly requested. No commit unless explicitly requested.
- Do not create pull requests for this project. When explicitly authorized to
  publish a validated release, publish it directly without a PR.

## Completion

Before finishing:

1. Review the diff.
2. Run the tests relevant to the change.
3. Run `ruff check .`.
4. Report changed files and test results.
5. Report any remaining risk or manual verification required.
6. Do not commit unless explicitly requested.
7. If this change added/removed a model, field, status, or infra component, flag in your report that `docs/ARCHITECTURE.md` may need updating — do not edit it yourself unless asked.
