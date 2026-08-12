import logging
import smtplib

from django.conf import settings
from django.contrib.auth import (
    authenticate,
    login,
)
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache

from economy.auth import current_child
from economy.changelog import load_changelog
from economy.email_config import save_smtp_config, verify_smtp
from economy.forms import (
    InitialSetupForm,
)
from economy.models import (
    AttemptCounter,
    FamilySettings,
)
from economy.net import client_ip
from economy.rate_limit import register_attempt
from economy.setup import (
    SetupUnavailable,
    complete_setup,
    setup_is_available,
    setup_token_meets_entropy_floor,
    token_is_valid,
)

logger = logging.getLogger("economy.views")


def health(request):
    return JsonResponse({"status": "ok", "version": settings.APP_VERSION})

def changelog(request):
    release_page = Paginator(load_changelog(), 5).get_page(
        request.GET.get("page", 1)
    )
    return render(
        request,
        "economy/changelog.html",
        {
            "releases": release_page.object_list,
            "release_page": release_page,
            "current_version": settings.APP_VERSION,
        },
    )

def home(request):
    if request.user.is_authenticated:
        return redirect("parent_dashboard")
    if current_child(request):
        return redirect("child_dashboard")
    return render(request, "economy/home.html")

@never_cache
def setup(request):
    if not setup_is_available():
        return redirect("parent_dashboard" if request.user.is_authenticated else "parent_login")
    if request.method == "POST":
        form = InitialSetupForm(request.POST)
        if not register_attempt(
            AttemptCounter.Scope.SETUP_CLAIM_IP,
            client_ip(request),
            window_seconds=300,
            limit=10,
        ):
            form.add_error(
                None,
                _("Too many setup attempts. Try again later."),
            )
            return render(request, "economy/setup.html", {"form": form})
        if form.is_valid():
            if not setup_token_meets_entropy_floor(settings.SETUP_TOKEN):
                form.add_error(
                    "setup_token",
                    _(
                        "The configured setup code is too short. "
                        "Ask the server administrator to generate a longer code."
                    ),
                )
            elif not token_is_valid(form.cleaned_data["setup_token"]):
                form.add_error("setup_token", _("The setup code is incorrect."))
            else:
                smtp = None
                if form.cleaned_data["configure_smtp"]:
                    smtp = {
                        "enabled": True,
                        "host": form.cleaned_data["smtp_host"],
                        "port": form.cleaned_data["smtp_port"],
                        "security": form.cleaned_data["smtp_security"],
                        "username": form.cleaned_data["smtp_username"],
                        "password": form.cleaned_data["smtp_password"],
                        "from_email": form.cleaned_data["smtp_from_email"],
                        "feedback_email": form.cleaned_data["smtp_feedback_email"],
                    }
                    try:
                        verify_smtp(smtp)
                    except (OSError, ValueError, smtplib.SMTPException):
                        form.add_error(None, _("Email settings were not saved. Check the server details and credentials."))
                        return render(request, "economy/setup.html", {"form": form})
                try:
                    result = complete_setup(
                        username=form.cleaned_data["username"],
                        email=form.cleaned_data["email"],
                        password=form.cleaned_data["password1"],
                        family_name=form.cleaned_data["family_name"],
                        language=form.cleaned_data["default_language"],
                        timezone_name=form.cleaned_data["timezone_name"],
                    )
                except SetupUnavailable:
                    return redirect("parent_login")
                if smtp is not None:
                    try:
                        save_smtp_config(smtp)
                    except OSError:
                        logger.warning("SMTP settings could not be saved after setup", exc_info=True)
                user = authenticate(
                    request,
                    username=form.cleaned_data["username"],
                    password=form.cleaned_data["password1"],
                )
                if user is not None:
                    login(request, user)
                    request.session.set_expiry(settings.PARENT_SESSION_SECONDS)
                response = render(
                    request,
                    "economy/setup_complete.html",
                    {"recovery_code": result.recovery_code},
                )
                response.set_cookie(
                    settings.LANGUAGE_COOKIE_NAME,
                    form.cleaned_data["default_language"],
                )
                return response
    else:
        form = InitialSetupForm(initial={"default_language": settings.LANGUAGE_CODE})
    return render(request, "economy/setup.html", {"form": form})

def manifest(request):
    family = FamilySettings.load()
    return JsonResponse(
        {
            "name": family.display_name,
            "short_name": family.family_name or str(_("Family")),
            "id": "/",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#F9FAFB",
            "theme_color": "#4C1D95",
            "icons": [
                {
                    "src": f"/static/icons/icon-192.png?v={settings.APP_VERSION}",
                    "sizes": "192x192",
                    "type": "image/png",
                },
                {
                    "src": f"/static/icons/icon-512.png?v={settings.APP_VERSION}",
                    "sizes": "512x512",
                    "type": "image/png",
                },
            ],
        },
        content_type="application/manifest+json",
    )

def service_worker(request):
    response = render(request, "economy/service-worker.js", content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response
