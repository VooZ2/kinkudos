#!/usr/bin/env python3
"""Validate KinKudos and create one clean, checksummed release archive."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "backups",
    "backup-state",
    "data",
    "dist",
    "secrets",
    "staticfiles",
}
EXCLUDED_NAMES = {".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".sqlite3"}
EXCLUDED_PART_PREFIXES = ("release-",)
REQUIRED_DEPLOY_FILES = {
    Path("deploy/compose.yml"),
    Path("deploy/compose.hostinger.yml"),
    Path("deploy/hostinger-bootstrap.sh"),
    Path("deploy/hostinger-healthcheck.sh"),
    Path("deploy/install-hostinger.sh"),
    Path("deploy/install.sh"),
}


def run(
    *command: str,
    env: dict[str, str] | None = None,
    cwd: Path = ROOT,
) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def project_version() -> str:
    source = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^version = "([^"]+)"$', source)
    if not match:
        raise SystemExit("Could not read the version from pyproject.toml.")
    version = match.group(1)
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise SystemExit(f"Invalid release version: {version}")
    return version


def included_files() -> list[Path]:
    tracked = subprocess.run(
        ("git", "ls-files", "-z"),
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")
    files = []
    for encoded_relative in tracked:
        if not encoded_relative:
            continue
        relative = Path(os.fsdecode(encoded_relative))
        path = ROOT / relative
        if (
            any(part in EXCLUDED_PARTS for part in relative.parts)
            and relative not in REQUIRED_DEPLOY_FILES
        ):
            continue
        if any(
            part.startswith(EXCLUDED_PART_PREFIXES) for part in relative.parts
        ):
            continue
        if path.is_symlink() or not path.is_file():
            continue
        if path.name in EXCLUDED_NAMES or path.suffix in EXCLUDED_SUFFIXES:
            continue
        if relative == Path("deploy/.env"):
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    version = project_version()
    python = str(ROOT / ".venv" / "bin" / "python")
    if not Path(python).is_file():
        raise SystemExit("Project virtual environment is missing: .venv/bin/python")

    run(python, "scripts/verify_release.py")
    run(python, "scripts/compile_translations.py")
    run(python, "manage.py", "check")

    with tempfile.TemporaryDirectory(prefix="kinkudos-release-check-") as temporary:
        check_env = os.environ.copy()
        check_env.update(
            {
                "KINKUDOS_DEBUG": "true",
                "KINKUDOS_DATABASE_PATH": str(Path(temporary) / "check.sqlite3"),
                "KINKUDOS_LOG_LEVEL": "CRITICAL",
            }
        )
        run(
            python,
            "manage.py",
            "makemigrations",
            "--check",
            "--dry-run",
            env=check_env,
        )
        run(python, "manage.py", "test", "--verbosity", "1", env=check_env)

    DIST.mkdir(exist_ok=True)
    archive = DIST / f"kinkudos-{version}.tar.gz"
    temporary_archive = DIST / f".kinkudos-{version}.tar.gz.tmp"
    temporary_archive.unlink(missing_ok=True)

    prefix = Path(f"kinkudos-{version}")
    with tarfile.open(temporary_archive, "w:gz", format=tarfile.PAX_FORMAT) as bundle:
        for path in included_files():
            relative = path.relative_to(ROOT)
            bundle.add(path, arcname=(prefix / relative).as_posix(), recursive=False)

    with tempfile.TemporaryDirectory(prefix="kinkudos-archive-check-") as temporary:
        extracted_root = Path(temporary)
        with tarfile.open(temporary_archive, "r:gz") as bundle:
            bundle.extractall(extracted_root, filter="data")
        packaged_project = extracted_root / prefix
        run(python, "scripts/verify_release.py", cwd=packaged_project)

    temporary_archive.replace(archive)
    digest = sha256(archive)
    checksum = archive.with_suffix(archive.suffix + ".sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")

    print(f"Release archive: {archive}")
    print(f"Checksum file:  {checksum}")
    print(f"SHA256:         {digest}")


if __name__ == "__main__":
    main()
