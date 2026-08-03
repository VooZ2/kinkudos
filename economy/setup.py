import secrets
from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import OperationalError, transaction
from django.utils import timezone

from .models import ChildProfile, FamilySettings


class SetupUnavailable(Exception):
    pass


@dataclass(frozen=True)
class SetupResult:
    recovery_code: str


def setup_is_available():
    return (
        not get_user_model().objects.exists()
        and not ChildProfile.objects.exists()
        and FamilySettings.load().setup_completed_at is None
    )


def token_is_valid(value):
    expected = settings.SETUP_TOKEN
    return bool(expected and value and secrets.compare_digest(expected, value))


def complete_setup(*, username, email, password, family_name, language, timezone_name):
    """Create the only bootstrap account and family state as one DB change."""
    User = get_user_model()
    try:
        with transaction.atomic():
            family = FamilySettings.load()
            # This conditional write is the cross-worker setup claim. SQLite serializes it.
            claimed = FamilySettings.objects.filter(
                pk=family.pk, setup_completed_at__isnull=True
            ).update(setup_completed_at=timezone.now())
            if not claimed or User.objects.exists() or ChildProfile.objects.exists():
                raise SetupUnavailable
            recovery_code = secrets.token_urlsafe(24)
            family.refresh_from_db()
            family.family_name = family_name
            family.default_language = language
            family.timezone_name = timezone_name
            family.recovery_code_hash = make_password(recovery_code)
            family.save(
                update_fields=[
                    "family_name",
                    "default_language",
                    "timezone_name",
                    "recovery_code_hash",
                ]
            )
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True,
            )
    except OperationalError as exc:
        raise SetupUnavailable from exc
    return SetupResult(recovery_code=recovery_code)
