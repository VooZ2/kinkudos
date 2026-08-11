import base64
import ipaddress
import secrets

from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone

from .auth import current_child
from .models import AttemptCounter, FamilySettings
from .net import FORWARDED_HEADERS, client_ip, direct_peer_is_trusted, parse_allowed_networks
from .rate_limit import register_attempt
from .setup import setup_is_available


class ContentSecurityPolicyMiddleware:
    """Attach a nonce-based policy to every application response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        nonce = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
        request.csp_nonce = nonce
        response = self.get_response(request)
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "base-uri 'self'; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "img-src 'self' data: blob:; "
            "manifest-src 'self'; "
            "object-src 'none'; "
            f"script-src 'self' 'nonce-{nonce}'; "
            "style-src 'self' 'unsafe-inline'; "
            "worker-src 'self'"
        )
        return response


class DeviceCookieRefreshMiddleware:
    """Keep an actively used paired-device cookie from expiring silently."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        device = getattr(request, "_kinkudos_device", None)
        raw_token = request.COOKIES.get(settings.DEVICE_COOKIE_NAME)
        if device is not None and raw_token:
            response.set_cookie(
                settings.DEVICE_COOKIE_NAME,
                raw_token,
                max_age=settings.DEVICE_COOKIE_MAX_AGE,
                secure=settings.SESSION_COOKIE_SECURE,
                httponly=True,
                samesite="Lax",
                path="/",
            )
        return response


class SetupRequiredMiddleware:
    public_prefixes = (
        "/setup/",
        "/health/",
        "/static/",
        "/manifest.webmanifest",
        "/service-worker.js",
        "/i18n/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(self.public_prefixes):
            return self.get_response(request)
        if setup_is_available():
            return redirect("setup")
        return self.get_response(request)


class DefaultLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.LANGUAGE_COOKIE_NAME not in request.COOKIES:
            language = FamilySettings.load().default_language
            if language:
                request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = language
        return self.get_response(request)


class FamilyTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        zone = FamilySettings.load().timezone_name or settings.TIME_ZONE
        timezone.activate(zone)
        try:
            return self.get_response(request)
        finally:
            timezone.deactivate()


class TrustedProxyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not direct_peer_is_trusted(request):
            for header in FORWARDED_HEADERS:
                request.META.pop(header, None)
        return self.get_response(request)


class NetworkAccessMiddleware:
    always_public_prefixes = (
        "/health/",
        "/static/",
        "/manifest.webmanifest",
        "/service-worker.js",
    )
    child_prefixes = (
        "/child/",
        "/vaikas/",
        "/pair-device/",
        "/susieti-irengini/",
    )
    parent_auth_prefixes = (
        "/login/",
        "/prisijungti/",
        "/password/reset/",
        "/password/new/",
        "/password/changed/",
        "/slaptazodis/atkurti/",
        "/slaptazodis/issiusta/",
        "/slaptazodis/naujas/",
        "/slaptazodis/pakeistas/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(self.always_public_prefixes):
            return self.get_response(request)
        family = FamilySettings.load()
        mode = family.network_access_mode
        authenticated_parent = getattr(request.user, "is_authenticated", False)
        active_child = None if authenticated_parent else current_child(request)
        restricted = mode == FamilySettings.NetworkAccessMode.ALL or (
            mode == FamilySettings.NetworkAccessMode.CHILDREN
            and (
                not request.path.startswith(self.parent_auth_prefixes)
                and (
                    request.path.startswith(self.child_prefixes)
                    or active_child is not None
                )
            )
        )
        if restricted:
            networks, _errors = parse_allowed_networks(family.allowed_networks)
            address = client_ip(request)
            if not any(
                address != "invalid" and ipaddress.ip_address(address) in network
                for network in networks
            ):
                return render(request, "economy/network_denied.html", status=403)
        return self.get_response(request)


class AdminRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/admin/login/" and request.method == "POST":
            allowed = register_attempt(
                AttemptCounter.Scope.ADMIN_LOGIN_IP,
                client_ip(request),
                window_seconds=300,
                limit=10,
            )
            if not allowed:
                return HttpResponseForbidden("Too many sign-in attempts.")
        return self.get_response(request)
