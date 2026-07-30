#!/usr/bin/env python3
"""Isolated KinKudos backup scheduler and control API."""

from __future__ import annotations

import hmac
import json
import os
import sqlite3
import subprocess
import threading
import time
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import NamedTemporaryFile

STATE_PATH = Path(os.environ.get("KINKUDOS_BACKUP_STATE_PATH", "/state/status.json"))
ENV_PATH = Path(os.environ.get("KINKUDOS_RESTIC_ENV_FILE", "/run/backup/restic.env"))
PASSWORD_FILE = os.environ.get(
    "KINKUDOS_RESTIC_PASSWORD_FILE", "/run/secrets/restic_password"
)
DATABASE_PATH = Path(
    os.environ.get("KINKUDOS_BACKUP_DATABASE_PATH", "/source/kinkudos.sqlite3")
)
MEDIA_PATH = Path(os.environ.get("KINKUDOS_BACKUP_MEDIA_PATH", "/source/media"))
OUTPUT_DIR = Path(os.environ.get("KINKUDOS_BACKUP_OUTPUT_DIR", "/backups"))
TOKEN_FILE = Path(
    os.environ.get("KINKUDOS_BACKUP_AGENT_TOKEN_FILE", "/run/secrets/backup_agent_token")
)
BACKUP_HOUR = int(os.environ.get("KINKUDOS_BACKUP_HOUR", "3"))
LOCK = threading.Lock()


def now_iso():
    return datetime.now(UTC).isoformat()


def read_env(path):
    values = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def provider_from_repository(repository):
    if not repository or repository == "REPLACE_WITH_REPOSITORY":
        return ""
    if "backblazeb2.com" in repository:
        return "backblaze_s3"
    if repository.startswith("b2:"):
        return "backblaze_legacy"
    if repository.startswith("s3:"):
        return "s3"
    return "custom"


def public_target(repository):
    if not repository:
        return ""
    return repository.split("@", 1)[-1][:255]


def initial_status():
    env = read_env(ENV_PATH)
    repository = env.get("RESTIC_REPOSITORY", "")
    configured = bool(repository and repository != "REPLACE_WITH_REPOSITORY")
    return {
        "available": True,
        "configured": configured,
        "provider": provider_from_repository(repository),
        "target": public_target(repository) if configured else "",
        "key_hint": env.get("AWS_ACCESS_KEY_ID", "")[-4:],
        "running": False,
        "health": "unknown" if configured else "not_configured",
        "last_attempt_at": None,
        "last_success_at": None,
        "last_check_at": None,
        "last_scheduled_date": None,
        "error": "",
    }


def load_status():
    status = initial_status()
    try:
        saved = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return status
    status.update(saved)
    status["available"] = True
    status["running"] = False
    return status


STATUS = load_status()


def save_status():
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w", encoding="utf-8", dir=STATE_PATH.parent, delete=False
    ) as temporary:
        json.dump(STATUS, temporary, ensure_ascii=False)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    os.chmod(temporary_path, 0o600)
    temporary_path.replace(STATE_PATH)


def restic_environment(path=None):
    path = path or ENV_PATH
    environment = os.environ.copy()
    environment.update(read_env(path))
    environment["RESTIC_PASSWORD_FILE"] = PASSWORD_FILE
    return environment


def run_command(command, *, env=None):
    return subprocess.run(
        command,
        env=env,
        capture_output=True,
        text=True,
        timeout=60 * 60,
        check=False,
    )


def write_config(payload):
    provider = payload.get("provider")
    endpoint = str(payload.get("endpoint", "")).strip().removeprefix("https://")
    bucket = str(payload.get("bucket", "")).strip().strip("/")
    region = str(payload.get("region", "")).strip()
    access_key_id = str(payload.get("access_key_id", "")).strip()
    secret_access_key = str(payload.get("secret_access_key", "")).strip()
    if provider not in {"backblaze_s3", "s3"}:
        raise ValueError("Unsupported backup provider.")
    if not all((endpoint, bucket, access_key_id, secret_access_key)):
        raise ValueError("Endpoint, bucket, access key ID, and secret key are required.")
    if any(character.isspace() for character in endpoint + bucket):
        raise ValueError("Endpoint and bucket cannot contain whitespace.")
    repository = f"s3:https://{endpoint}/{bucket}/kinkudos"
    values = {
        "RESTIC_REPOSITORY": repository,
        "AWS_ACCESS_KEY_ID": access_key_id,
        "AWS_SECRET_ACCESS_KEY": secret_access_key,
    }
    if region:
        values["AWS_DEFAULT_REGION"] = region
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    previous = ENV_PATH.read_bytes() if ENV_PATH.exists() else None
    with NamedTemporaryFile("w", encoding="utf-8", dir=ENV_PATH.parent, delete=False) as temp:
        temp.write("# Managed by the KinKudos backup agent. Do not commit.\n")
        for key, value in values.items():
            temp.write(f"{key}={value}\n")
        temp_path = Path(temp.name)
    os.chmod(temp_path, 0o600)
    temp_path.replace(ENV_PATH)
    environment = restic_environment()
    probe = run_command(["restic", "snapshots", "--json"], env=environment)
    if probe.returncode != 0:
        initialized = run_command(["restic", "init"], env=environment)
        if initialized.returncode != 0:
            if previous is None:
                ENV_PATH.unlink(missing_ok=True)
            else:
                ENV_PATH.write_bytes(previous)
                os.chmod(ENV_PATH, 0o600)
            detail = (initialized.stderr or probe.stderr or "Repository check failed.").strip()
            raise ValueError(detail[-500:])
    return repository, access_key_id[-4:]


def create_database_backup():
    if not DATABASE_PATH.is_file():
        raise RuntimeError("KinKudos database was not found.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    local_now = datetime.now().astimezone()
    destination = OUTPUT_DIR / f"kinkudos-{local_now:%Y%m%d-%H%M%S}.sqlite3"
    with sqlite3.connect(DATABASE_PATH) as source, sqlite3.connect(destination) as target:
        source.backup(target)
        result = target.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"Database integrity check failed: {result}")
    cutoff = local_now - timedelta(days=31)
    for candidate in OUTPUT_DIR.glob("kinkudos-*.sqlite3"):
        if datetime.fromtimestamp(candidate.stat().st_mtime, tz=local_now.tzinfo) < cutoff:
            candidate.unlink()
    return destination


def perform_backup(*, scheduled=False, lock_acquired=False):
    if not lock_acquired and not LOCK.acquire(blocking=False):
        raise RuntimeError("A backup is already running.")
    try:
        STATUS.update(
            {
                "running": True,
                "last_attempt_at": now_iso(),
                "error": "",
            }
        )
        if scheduled:
            STATUS["last_scheduled_date"] = datetime.now().astimezone().date().isoformat()
        save_status()
        env = restic_environment()
        if not env.get("RESTIC_REPOSITORY") or env["RESTIC_REPOSITORY"] == "REPLACE_WITH_REPOSITORY":
            raise RuntimeError("Backup repository is not configured.")
        database_backup = create_database_backup()
        sources = [str(database_backup)]
        if MEDIA_PATH.is_dir():
            sources.append(str(MEDIA_PATH))
        backup = run_command(["restic", "backup", *sources, "--tag", "kinkudos"], env=env)
        if backup.returncode != 0:
            raise RuntimeError((backup.stderr or backup.stdout).strip()[-500:])
        forget = run_command(
            [
                "restic",
                "forget",
                "--tag",
                "kinkudos",
                "--keep-daily",
                "31",
                "--prune",
            ],
            env=env,
        )
        if forget.returncode != 0:
            raise RuntimeError((forget.stderr or forget.stdout).strip()[-500:])
        checked = run_command(["restic", "check"], env=env)
        if checked.returncode != 0:
            raise RuntimeError((checked.stderr or checked.stdout).strip()[-500:])
        STATUS.update(
            {
                "configured": True,
                "health": "healthy",
                "last_success_at": now_iso(),
                "last_check_at": now_iso(),
                "error": "",
            }
        )
    # The daemon records any command, filesystem, or configuration failure in
    # status instead of terminating its scheduler thread.
    except Exception as exc:  # noqa: BLE001
        STATUS.update({"health": "error", "error": str(exc)[-500:]})
    finally:
        STATUS["running"] = False
        save_status()
        LOCK.release()


def probe_existing_repository():
    if not STATUS.get("configured") or not LOCK.acquire(blocking=False):
        return
    try:
        result = run_command(["restic", "snapshots", "--json"], env=restic_environment())
        if result.returncode != 0:
            STATUS.update(
                {
                    "health": "error",
                    "error": (result.stderr or result.stdout).strip()[-500:],
                }
            )
            return
        snapshots = json.loads(result.stdout or "[]")
        times = [snapshot.get("time") for snapshot in snapshots if snapshot.get("time")]
        if times:
            STATUS["last_success_at"] = max(times)
            STATUS["health"] = "healthy"
        else:
            STATUS["health"] = "ready"
        STATUS["error"] = ""
    except (json.JSONDecodeError, OSError) as exc:
        STATUS.update({"health": "error", "error": str(exc)[-500:]})
    finally:
        save_status()
        LOCK.release()


def schedule_loop():
    while True:
        local_now = datetime.now().astimezone()
        today = local_now.date().isoformat()
        if (
            STATUS.get("configured")
            and local_now.hour >= BACKUP_HOUR
            and STATUS.get("last_scheduled_date") != today
        ):
            perform_backup(scheduled=True)
        time.sleep(60)


class Handler(BaseHTTPRequestHandler):
    server_version = "KinKudosBackup/1"

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}", flush=True)

    def authorized(self):
        supplied = self.headers.get("Authorization", "")
        expected = f"Bearer {TOKEN_FILE.read_text(encoding='utf-8').strip()}"
        return hmac.compare_digest(supplied, expected)

    def respond(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_payload(self):
        length = min(int(self.headers.get("Content-Length", "0")), 16 * 1024)
        return json.loads(self.rfile.read(length).decode("utf-8") or "{}")

    def do_GET(self):
        if not self.authorized():
            self.respond(403, {"error": "Forbidden."})
            return
        if self.path == "/status":
            self.respond(200, STATUS)
        else:
            self.respond(404, {"error": "Not found."})

    def do_POST(self):
        if not self.authorized():
            self.respond(403, {"error": "Forbidden."})
            return
        try:
            payload = self.read_payload()
            if self.path == "/configure":
                if not LOCK.acquire(blocking=False):
                    raise ValueError("A backup is currently running.")
                try:
                    repository, key_hint = write_config(payload)
                    STATUS.update(
                        {
                            "configured": True,
                            "provider": payload["provider"],
                            "target": public_target(repository),
                            "key_hint": key_hint,
                            "health": "ready",
                            "error": "",
                        }
                    )
                    save_status()
                finally:
                    LOCK.release()
                self.respond(200, STATUS)
                return
            if self.path == "/run":
                if not LOCK.acquire(blocking=False):
                    raise ValueError("A backup is already running.")
                threading.Thread(
                    target=perform_backup,
                    kwargs={"lock_acquired": True},
                    daemon=True,
                ).start()
                self.respond(202, {"accepted": True})
                return
            self.respond(404, {"error": "Not found."})
        except (ValueError, json.JSONDecodeError) as exc:
            self.respond(400, {"error": str(exc)})


def main():
    if not TOKEN_FILE.is_file():
        raise SystemExit("Backup agent token is missing.")
    save_status()
    threading.Thread(target=probe_existing_repository, daemon=True).start()
    threading.Thread(target=schedule_loop, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", 8090), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
