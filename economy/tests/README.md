# Economy test suite

Tests are grouped by the system domain they protect, not by the bug, patch, or
release history that first exposed the behaviour. Regression tests belong in
the closest domain file and should be named after the invariant they verify.

Main responsibilities:

- `test_auth.py` — parent account permissions and administrator boundaries.
- `test_services.py` — transactional business operations, ledger effects, and
  state transitions.
- `test_models.py` — model validation and database-level model invariants.
- `test_push.py` — Web Push validation, ownership, delivery, and limits.
- `test_security_controls.py` — network access, request security, and rate
  limits.
- `test_backups.py` / `test_backup_agent.py` — backup configuration and the
  isolated scheduler/agent.
- `test_release_deployment.py` — Compose, installer, migration, and release
  validation contracts.
- `test_views.py` and the focused workflow files — user-facing request and
  dashboard behaviour.

Put a new regression test beside the domain operation it protects. Use
`TestCase` for ordinary isolated database behaviour. Use `TransactionTestCase`
only when the test must exercise transaction boundaries or database-level
concurrency semantics that `TestCase` wraps in a transaction; SQLite tests
should assert the atomic conditional invariant they can reliably exercise.
