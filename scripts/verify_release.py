"""Fail early when a release contains an incomplete migration or version mismatch."""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def version_from(path: Path, pattern: str) -> str:
    match = re.search(pattern, path.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit(f"Could not read the version from {path.relative_to(ROOT)}")
    for group in match.groups():
        if group is not None:
            return group
    raise SystemExit(f"Could not read the version from {path.relative_to(ROOT)}")


dockerignore_rules = {
    line.strip().rstrip("/")
    for line in (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.lstrip().startswith("#")
}
if "deploy" in dockerignore_rules:
    raise SystemExit(
        ".dockerignore must not exclude deploy because the Docker build "
        "validates deploy/compose.yml."
    )


versions = {
    "pyproject.toml": version_from(
        ROOT / "pyproject.toml", r'(?m)^version = "([^"]+)"$'
    ),
    "kinkudos/settings.py": version_from(
        ROOT / "kinkudos/settings.py",
        r'KINKUDOS_APP_VERSION", "([^"]+)"',
    ),
    "deploy/compose.yml": version_from(
        ROOT / "deploy" / "compose.yml",
        r"(?m)^\s*image: vooz2/kinkudos:(?:([0-9]+\.[0-9]+\.[0-9]+)|\$\{KINKUDOS_IMAGE_TAG:-([0-9]+\.[0-9]+\.[0-9]+)\})\s*$",
    ),
    "deploy/hostinger/compose.yaml": version_from(
        ROOT / "deploy" / "hostinger" / "compose.yaml",
        r"(?m)^\s*image: vooz2/kinkudos:(?:([0-9]+\.[0-9]+\.[0-9]+)|\$\{KINKUDOS_IMAGE_TAG:-([0-9]+\.[0-9]+\.[0-9]+)\})\s*$",
    ),
}
if len(set(versions.values())) != 1:
    raise SystemExit(f"Release versions do not match: {versions}")

public_installer = ROOT / "deploy" / "install.sh"
if not public_installer.is_file():
    raise SystemExit("The public installer is missing: deploy/install.sh")
if not os.access(public_installer, os.X_OK):
    raise SystemExit("The public installer is not executable: deploy/install.sh")

migrations_dir = ROOT / "economy" / "migrations"
conflicting_packages = sorted(
    path.name
    for path in migrations_dir.iterdir()
    if path.is_dir() and path.name[:1].isdigit()
)
if conflicting_packages:
    raise SystemExit(
        "Migration files are shadowed by conflicting package directories: "
        + ", ".join(conflicting_packages)
    )

migration_files = sorted(migrations_dir.glob("[0-9]*.py"))
if not migration_files:
    raise SystemExit("No Django migration files were included in this release.")
if not (migrations_dir / "0001_initial.py").is_file():
    raise SystemExit("The initial Django migration is missing.")

for migration in migration_files:
    source = migration.read_text(encoding="utf-8")
    if not source.strip():
        raise SystemExit(f"Migration is empty: {migration.name}")
    try:
        tree = ast.parse(source, filename=str(migration))
    except SyntaxError as exc:
        raise SystemExit(f"Migration is invalid: {migration.name}: {exc}") from exc
    if not any(
        isinstance(node, ast.ClassDef) and node.name == "Migration"
        for node in tree.body
    ):
        raise SystemExit(f"Migration has no Migration class: {migration.name}")

print(f"Release {next(iter(versions.values()))} and all migrations are valid.")
