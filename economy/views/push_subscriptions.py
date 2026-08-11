import json

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from economy.auth import child_required, current_device, parent_required
from economy.models import (
    CHILD_PUSH_SUBSCRIPTION_LIMIT,
    PARENT_PUSH_SUBSCRIPTION_LIMIT,
    DeviceToken,
    PushSubscription,
    validate_push_subscription_data,
)


def _push_payload(request):
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError
        keys = payload["keys"]
        if not isinstance(keys, dict):
            raise ValueError
        endpoint, p256dh, auth = validate_push_subscription_data(
            payload["endpoint"],
            keys["p256dh"],
            keys["auth"],
        )
    except (KeyError, TypeError, ValueError, UnicodeDecodeError, ValidationError):
        return None
    return endpoint, p256dh, auth

@parent_required
@require_POST
def push_subscribe(request):
    payload = _push_payload(request)
    if payload is None:
        return JsonResponse({"ok": False}, status=400)
    endpoint, p256dh, auth = payload
    with transaction.atomic():
        existing = PushSubscription.objects.filter(endpoint=endpoint).first()
        if (
            existing is None
            or existing.user_id != request.user.pk
            or existing.child_id is not None
        ) and PushSubscription.objects.filter(user=request.user).count() >= PARENT_PUSH_SUBSCRIPTION_LIMIT:
            return JsonResponse({"ok": False}, status=429)
        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                "user": request.user,
                "child": None,
                "device": None,
                "p256dh": p256dh,
                "auth": auth,
                "user_agent": request.headers.get("User-Agent", "")[:255],
            },
        )
    return JsonResponse({"ok": True})

@parent_required
@require_POST
def push_unsubscribe(request):
    try:
        endpoint = json.loads(request.body)["endpoint"]
    except (KeyError, TypeError, ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False}, status=400)
    PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
    return JsonResponse({"ok": True})

@child_required
@require_POST
def child_push_subscribe(request):
    payload = _push_payload(request)
    if payload is None:
        return JsonResponse({"ok": False}, status=400)
    endpoint, p256dh, auth = payload
    device = current_device(request)
    if device is None and settings.DEVICE_PAIRING_REQUIRED:
        return JsonResponse({"ok": False}, status=403)
    if device is None:
        device, _unused_token = DeviceToken.issue(
            created_by=None,
            label=_("Development device"),
        )
    with transaction.atomic():
        existing = PushSubscription.objects.filter(endpoint=endpoint).first()
        same_device = (
            existing is not None
            and existing.child_id == request.child.pk
            and existing.device_id == device.pk
        )
        if not same_device and PushSubscription.objects.filter(
            child=request.child,
            device=device,
        ).count() >= CHILD_PUSH_SUBSCRIPTION_LIMIT:
            return JsonResponse({"ok": False}, status=429)
        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                "user": None,
                "child": request.child,
                "device": device,
                "p256dh": p256dh,
                "auth": auth,
                "user_agent": request.headers.get("User-Agent", "")[:255],
            },
        )
    return JsonResponse({"ok": True})

@child_required
@require_POST
def child_push_unsubscribe(request):
    try:
        endpoint = json.loads(request.body)["endpoint"]
    except (KeyError, TypeError, ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False}, status=400)
    PushSubscription.objects.filter(
        child=request.child,
        device=current_device(request),
        endpoint=endpoint,
    ).delete()
    return JsonResponse({"ok": True})
