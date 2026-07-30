import json
import logging
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)


def _request(path, *, payload=None, timeout=3):
    if not settings.BACKUP_AGENT_URL or not settings.BACKUP_AGENT_TOKEN:
        raise RuntimeError("Backup agent is not configured.")
    body = None
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.BACKUP_AGENT_TOKEN}",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(
        f"{settings.BACKUP_AGENT_URL.rstrip('/')}{path}",
        data=body,
        headers=headers,
        method="POST" if payload is not None else "GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8")).get("error")
        except (ValueError, UnicodeDecodeError):
            detail = None
        raise RuntimeError(detail or "Backup agent rejected the request.") from exc
    except (URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError("Backup agent is unavailable.") from exc


def backup_status():
    try:
        status = _request("/status", timeout=1.5)
    except RuntimeError as exc:
        log = logger.warning if settings.BACKUP_AGENT_URL else logger.debug
        log("Could not read backup status: %s", exc)
        status = {
            "available": False,
            "configured": False,
            "running": False,
            "health": "unavailable",
            "error": str(exc),
        }
    last_success = parse_datetime(status.get("last_success_at") or "")
    status["is_fresh"] = bool(
        last_success and last_success >= timezone.now() - timedelta(days=7)
    )
    status["last_success"] = last_success
    status["last_attempt"] = parse_datetime(status.get("last_attempt_at") or "")
    status["last_check"] = parse_datetime(status.get("last_check_at") or "")
    return status


def configure_backup(cleaned_data):
    return _request(
        "/configure",
        payload={
            "provider": cleaned_data["provider"],
            "endpoint": cleaned_data["endpoint"],
            "bucket": cleaned_data["bucket"],
            "region": cleaned_data["region"],
            "access_key_id": cleaned_data["access_key_id"],
            "secret_access_key": cleaned_data["secret_access_key"],
        },
        timeout=45,
    )


def request_manual_backup():
    return _request("/run", payload={}, timeout=5)
