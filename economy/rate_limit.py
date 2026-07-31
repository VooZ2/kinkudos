import hashlib
import hmac
from datetime import UTC, datetime

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F

from .models import AttemptCounter


def key_hash(scope, value):
    payload = f"{scope}:{value}".encode()
    return hmac.new(
        settings.SECRET_KEY.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()


def _window_start(now, window_seconds):
    timestamp = int(now.timestamp())
    floored = timestamp - (timestamp % window_seconds)
    return datetime.fromtimestamp(floored, tz=UTC)


def register_attempt(scope, value, *, window_seconds, limit, now=None):
    from django.utils import timezone

    now = now or timezone.now()
    digest = key_hash(scope, value)
    window_start = _window_start(now, window_seconds)
    lookup = {
        "scope": scope,
        "key_hash": digest,
        "window_start": window_start,
    }
    with transaction.atomic():
        updated = AttemptCounter.objects.filter(**lookup).update(count=F("count") + 1)
        if not updated:
            try:
                # Keep the uniqueness race inside a savepoint so catching the
                # IntegrityError does not poison the surrounding transaction.
                with transaction.atomic():
                    AttemptCounter.objects.create(**lookup, count=1)
            except IntegrityError:
                AttemptCounter.objects.filter(**lookup).update(count=F("count") + 1)
        count = AttemptCounter.objects.values_list("count", flat=True).get(**lookup)
    return count <= limit


def reset_attempts(scope, value):
    AttemptCounter.objects.filter(
        scope=scope,
        key_hash=key_hash(scope, value),
    ).delete()
