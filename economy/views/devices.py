
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
)
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from economy.auth import parent_account_required
from economy.models import (
    AttemptCounter,
    DevicePairingLink,
    DeviceToken,
    PushSubscription,
    SecurityAuditEvent,
)
from economy.net import client_ip
from economy.rate_limit import register_attempt


@parent_account_required
@require_POST
def parent_pair_device(request):
    label = request.POST.get("label", "").strip()
    actor = request.user
    device, raw_token = DeviceToken.issue(
        created_by=actor,
        label=label,
        user_agent=request.headers.get("User-Agent", ""),
    )
    SecurityAuditEvent.objects.create(
        actor=actor,
        action=SecurityAuditEvent.Action.DEVICE_PAIRED,
        detail=device.display_name,
    )
    request.session.flush()
    response = redirect("child_select")
    response.set_cookie(
        settings.DEVICE_COOKIE_NAME,
        raw_token,
        max_age=settings.DEVICE_COOKIE_MAX_AGE,
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=True,
        samesite="Lax",
        path="/",
    )
    messages.success(
        request,
        _("This device is paired as %(device)s.") % {"device": device.display_name},
    )
    return response

@parent_account_required
@require_POST
def parent_generate_pairing_link(request):
    if not register_attempt(
        AttemptCounter.Scope.DEVICE_PAIRING,
        f"parent:{request.user.pk}",
        window_seconds=600,
        limit=10,
    ):
        messages.error(request, _("Too many pairing attempts. Try again later."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    link, raw_token = DevicePairingLink.issue(created_by=request.user)
    pairing_url = request.build_absolute_uri(reverse("pair_device_via_link"))
    request.session["device_pairing_share"] = {
        "pairing_url": f"{pairing_url}#{raw_token}",
        "expires_at": link.expires_at.isoformat(),
    }
    messages.success(request, _("The pairing link is ready to share."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")

@never_cache
def pair_device_via_link(request):
    if request.method == "GET":
        response = render(request, "economy/pair_device.html")
        response["Cache-Control"] = "no-store"
        response["Referrer-Policy"] = "same-origin"
        return response
    if not register_attempt(
        AttemptCounter.Scope.DEVICE_PAIRING,
        client_ip(request),
        window_seconds=600,
        limit=20,
    ):
        messages.error(request, _("Too many pairing attempts. Try again later."))
        return redirect("pair_device_via_link")
    raw_token = request.POST.get("token", "")
    with transaction.atomic():
        link = (
            DevicePairingLink.objects.select_for_update()
            .filter(token_hash=DeviceToken.digest(raw_token))
            .first()
        )
        if link is None or link.used_at is not None or link.expires_at <= timezone.now():
            messages.error(request, _("This pairing link is invalid or has expired."))
            return redirect("pair_device_via_link")
        device, device_token = DeviceToken.issue(
            created_by=link.created_by,
            user_agent=request.headers.get("User-Agent", ""),
        )
        link.used_at = timezone.now()
        link.save(update_fields=["used_at"])
        SecurityAuditEvent.objects.create(
            actor=link.created_by,
            action=SecurityAuditEvent.Action.DEVICE_PAIRED,
            detail=device.display_name,
        )
    request.session.flush()
    response = redirect("child_select")
    response.set_cookie(
        settings.DEVICE_COOKIE_NAME,
        device_token,
        max_age=settings.DEVICE_COOKIE_MAX_AGE,
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=True,
        samesite="Lax",
        path="/",
    )
    messages.success(
        request,
        _("This device is paired as %(device)s.") % {"device": device.display_name},
    )
    return response

@parent_account_required
@require_POST
def parent_revoke_device(request, device_id):
    device = get_object_or_404(DeviceToken, pk=device_id, revoked_at__isnull=True)
    with transaction.atomic():
        device.revoked_at = timezone.now()
        device.save(update_fields=["revoked_at"])
        device.push_subscriptions.all().delete()
        SecurityAuditEvent.objects.create(
            actor=request.user,
            action=SecurityAuditEvent.Action.DEVICE_REVOKED,
            detail=device.display_name,
        )
    messages.success(request, _("Device access revoked."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")

@parent_account_required
@require_POST
def parent_rename_device(request, device_id):
    device = get_object_or_404(DeviceToken, pk=device_id, revoked_at__isnull=True)
    label = request.POST.get("label", "").strip()
    if not label:
        messages.error(request, _("Enter a device name."))
    else:
        device.label = label[:80]
        device.save(update_fields=["label"])
        messages.success(request, _("Device name saved."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")

@parent_account_required
@require_POST
def parent_revoke_all_devices(request):
    if not request.user.is_staff:
        messages.error(
            request,
            _("Only a parent administrator can revoke all devices."),
        )
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    authenticated = authenticate(
        request,
        username=request.user.get_username(),
        password=request.POST.get("current_password", ""),
    )
    if authenticated is None:
        messages.error(request, _("The current parent password is incorrect."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    with transaction.atomic():
        devices = DeviceToken.objects.filter(revoked_at__isnull=True)
        PushSubscription.objects.filter(device__in=devices).delete()
        devices.update(revoked_at=timezone.now())
        SecurityAuditEvent.objects.create(
            actor=request.user,
            action=SecurityAuditEvent.Action.ALL_DEVICES_REVOKED,
        )
    messages.success(request, _("All child devices were revoked."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")
