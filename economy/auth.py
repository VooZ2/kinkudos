from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from .models import ChildProfile, DeviceToken


def current_device(request):
    if hasattr(request, "_kinkudos_device"):
        return request._kinkudos_device
    raw_token = request.COOKIES.get(settings.DEVICE_COOKIE_NAME, "")
    device = None
    if raw_token:
        device = DeviceToken.objects.filter(
            token_hash=DeviceToken.digest(raw_token),
            revoked_at__isnull=True,
        ).first()
        if device and (
            device.last_used_at is None
            or device.last_used_at < timezone.now() - timedelta(hours=1)
        ):
            DeviceToken.objects.filter(
                pk=device.pk,
                revoked_at__isnull=True,
                last_used_at=device.last_used_at,
            ).update(last_used_at=timezone.now())
    request._kinkudos_device = device
    return device


def current_child(request):
    child_id = request.session.get("child_id")
    if not child_id:
        return None
    device = current_device(request)
    if settings.DEVICE_PAIRING_REQUIRED and (
        device is None or request.session.get("child_device_id") != device.pk
    ):
        request.session.flush()
        return None
    try:
        return ChildProfile.objects.get(pk=child_id, is_active=True)
    except ChildProfile.DoesNotExist:
        request.session.flush()
        return None


def parent_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        return view(request, *args, **kwargs)

    return wrapped


def child_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        child = current_child(request)
        if child is None:
            return redirect("child_select")
        request.child = child
        if (
            not child.theme_selected
            and request.resolver_match
            and request.resolver_match.url_name != "child_theme_onboarding"
        ):
            return redirect("child_theme_onboarding")
        return view(request, *args, **kwargs)

    return wrapped


def child_object_or_404(request, queryset, **lookup):
    child = getattr(request, "child", None) or current_child(request)
    if child is None:
        raise Http404
    return get_object_or_404(queryset, child=child, **lookup)
