import json
import os
import smtplib
import ssl
from pathlib import Path
from tempfile import NamedTemporaryFile

from django.conf import settings

from economy.net import require_global_destination


def smtp_config():
    path = Path(settings.SMTP_CONFIG_PATH)
    if path.is_file():
        try:
            stored = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            stored = {}
        if stored:
            return stored
    return {
        "enabled": settings.EMAIL_ENABLED,
        "host": settings.EMAIL_HOST,
        "port": settings.EMAIL_PORT,
        "security": (
            "ssl" if settings.EMAIL_USE_SSL else "tls" if settings.EMAIL_USE_TLS else "none"
        ),
        "username": settings.EMAIL_HOST_USER,
        "password": settings.EMAIL_HOST_PASSWORD,
        "from_email": settings.DEFAULT_FROM_EMAIL,
        "feedback_email": settings.FEEDBACK_EMAIL,
    }


def public_smtp_config():
    config = smtp_config()
    return {
        "enabled": bool(config.get("enabled")),
        "host": str(config.get("host", "")),
        "port": int(config.get("port", 587)),
        "security": str(config.get("security", "tls")),
        "username": str(config.get("username", "")),
        "from_email": str(config.get("from_email", "")),
        "feedback_email": str(config.get("feedback_email", "")),
        "password_configured": bool(config.get("password")),
    }


def verify_smtp(config):
    require_global_destination(
        config["host"],
        config["port"],
        allow_private=settings.SMTP_ALLOW_PRIVATE_DESTINATIONS,
    )
    context = ssl.create_default_context()
    client_class = smtplib.SMTP_SSL if config["security"] == "ssl" else smtplib.SMTP
    with client_class(config["host"], config["port"], timeout=15) as client:
        if config["security"] == "tls":
            client.starttls(context=context)
        client.login(config["username"], config["password"])


def save_smtp_config(config):
    path = Path(settings.SMTP_CONFIG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    values = {
        "enabled": bool(config["enabled"]),
        "host": config["host"].strip(),
        "port": int(config["port"]),
        "security": config["security"],
        "username": config["username"].strip(),
        "password": config["password"],
        "from_email": config["from_email"].strip(),
        "feedback_email": config["feedback_email"].strip(),
    }
    with NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as temporary:
        json.dump(values, temporary)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    os.chmod(temporary_path, 0o600)
    temporary_path.replace(path)
