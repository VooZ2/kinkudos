from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from economy.auth import parent_account_required
from economy.email_config import smtp_config
from economy.forms import CaregiverCreatePinForm, CaregiverInviteForm, CaregiverPinForm
from economy.models import (
    AttemptCounter,
    CaregiverInvite,
    CaregiverProfile,
    DeviceToken,
    FamilySettings,
)
from economy.net import client_ip
from economy.rate_limit import register_attempt, reset_attempts


def caregiver_share_message(*, family_name):
    title = _("%(family)s – guest access") % {"family": family_name}
    text = _(
        "Hi! I'm sharing temporary access to our family space. "
        "This is a temporary sign-in link — keep it private. "
        "After you open it, create your own PIN so you can approve requests "
        "and assign day-to-day tasks."
    )
    return title, text


def _active_caregivers():
    today = timezone.localdate()
    return (
        CaregiverProfile.objects.filter(is_active=True, access_until__gte=today)
        .select_related("user")
        .prefetch_related("children")
        .order_by("label", "pk")
    )


def _pending_invites():
    return (
        CaregiverInvite.objects.filter(
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .select_related("created_by")
        .prefetch_related("children")
        .order_by("-created_at", "-pk")
    )


def caregiver_settings_context(request=None):
    share = None
    if request is not None:
        share = request.session.pop("caregiver_invite_share", None)
    return {
        "caregiver_invite_form": CaregiverInviteForm(auto_id="id_caregiver_invite_%s"),
        "active_caregivers": list(_active_caregivers()),
        "pending_caregiver_invites": list(_pending_invites()),
        "smtp_enabled_for_caregiver": bool(smtp_config().get("enabled")),
        "caregiver_invite_share": share,
    }


@parent_account_required
@require_POST
def parent_create_caregiver_invite(request):
    if not register_attempt(
        AttemptCounter.Scope.CAREGIVER_INVITE_PARENT,
        f"parent:{request.user.pk}",
        window_seconds=600,
        limit=10,
    ):
        messages.error(request, _("Too many guest invites. Try again later."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    form = CaregiverInviteForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Check the guest invite form."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    invite, raw_token = CaregiverInvite.issue(
        created_by=request.user,
        label=form.cleaned_data["label"],
        access_until=form.cleaned_data["access_until"],
        children=form.cleaned_data["children"],
        email=form.cleaned_data.get("email") or "",
    )
    invite_path = reverse("caregiver_invite_redeem")
    invite_url = f"{request.build_absolute_uri(invite_path)}#{raw_token}"
    family_name = FamilySettings.load().header_name
    share_title, share_text = caregiver_share_message(family_name=family_name)
    email_sent = False
    email_address = (form.cleaned_data.get("email") or "").strip()
    if email_address and smtp_config().get("enabled"):
        try:
            send_mail(
                share_title,
                f"{share_text}\n\n{invite_url}",
                smtp_config().get("from_email") or None,
                [email_address],
                fail_silently=False,
            )
            email_sent = True
        except Exception:
            messages.warning(
                request,
                _("The invite was created, but the email could not be sent."),
            )
    request.session["caregiver_invite_share"] = {
        "label": invite.label,
        "invite_url": invite_url,
        "share_title": share_title,
        "share_text": share_text,
        "email_sent": email_sent,
        "email_address": email_address,
    }
    messages.success(
        request,
        _("Guest invite for “%(name)s” is ready to share.") % {"name": invite.label},
    )
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")


@parent_account_required
@require_POST
def parent_cancel_caregiver_invite(request, invite_id):
    invite = get_object_or_404(CaregiverInvite, pk=invite_id, used_at__isnull=True)
    invite.expires_at = timezone.now()
    invite.save(update_fields=["expires_at"])
    messages.success(request, _("Guest invite cancelled."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")


@parent_account_required
@require_POST
def parent_remove_caregiver(request, caregiver_id):
    caregiver = get_object_or_404(CaregiverProfile, pk=caregiver_id, is_active=True)
    label = caregiver.label
    caregiver.deactivate()
    messages.success(
        request,
        _("Guest access for “%(name)s” was removed.") % {"name": label},
    )
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")


@parent_account_required
@require_POST
def parent_unlock_caregiver(request, caregiver_id):
    caregiver = get_object_or_404(CaregiverProfile, pk=caregiver_id, is_active=True)
    caregiver.failed_pin_attempts = 0
    caregiver.locked_until = None
    caregiver.save(update_fields=["failed_pin_attempts", "locked_until"])
    messages.success(
        request,
        _("“%(name)s” unlocked.") % {"name": caregiver.label},
    )
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")


@never_cache
@require_http_methods(["GET", "POST"])
def caregiver_invite_redeem(request):
    if request.method == "GET":
        response = render(request, "economy/caregiver_invite_landing.html")
        response["Cache-Control"] = "no-store"
        response["Referrer-Policy"] = "same-origin"
        return response

    if not register_attempt(
        AttemptCounter.Scope.CAREGIVER_INVITE_IP,
        client_ip(request),
        window_seconds=600,
        limit=20,
    ):
        messages.error(request, _("Too many attempts. Try again later."))
        return redirect("caregiver_invite_redeem")

    raw_token = request.POST.get("token", "")
    token_hash = DeviceToken.digest(raw_token)
    with transaction.atomic():
        invite = (
            CaregiverInvite.objects.select_for_update()
            .filter(token_hash=token_hash)
            .first()
        )
        if invite is None:
            messages.error(request, _("This sign-in link is invalid or has expired."))
            return redirect("caregiver_invite_redeem")
        if invite.used_at is not None and invite.caregiver_id:
            caregiver = invite.caregiver
            if caregiver is not None and caregiver.has_access:
                return redirect("caregiver_login", login_code=caregiver.login_code)
            messages.error(request, _("This sign-in link is invalid or has expired."))
            return redirect("caregiver_invite_redeem")
        if invite.used_at is not None or invite.expires_at <= timezone.now():
            messages.error(request, _("This sign-in link is invalid or has expired."))
            return redirect("caregiver_invite_redeem")
        request.session["caregiver_invite_token_hash"] = token_hash
        request.session["caregiver_invite_id"] = invite.pk
    return redirect("caregiver_create_pin")


def _pending_invite_from_session(request):
    invite_id = request.session.get("caregiver_invite_id")
    token_hash = request.session.get("caregiver_invite_token_hash")
    if not invite_id or not token_hash:
        return None
    invite = CaregiverInvite.objects.filter(pk=invite_id, token_hash=token_hash).first()
    if (
        invite is None
        or invite.used_at is not None
        or invite.expires_at <= timezone.now()
    ):
        request.session.pop("caregiver_invite_id", None)
        request.session.pop("caregiver_invite_token_hash", None)
        return None
    return invite


@never_cache
@require_http_methods(["GET", "POST"])
def caregiver_create_pin(request):
    invite = _pending_invite_from_session(request)
    if invite is None:
        messages.error(request, _("This sign-in link is invalid or has expired."))
        return redirect("caregiver_invite_redeem")

    if request.method == "GET":
        return render(
            request,
            "economy/caregiver_create_pin.html",
            {"form": CaregiverCreatePinForm(), "invite": invite},
        )

    form = CaregiverCreatePinForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "economy/caregiver_create_pin.html",
            {"form": form, "invite": invite},
        )

    with transaction.atomic():
        locked = (
            CaregiverInvite.objects.select_for_update()
            .filter(pk=invite.pk, token_hash=invite.token_hash)
            .first()
        )
        if (
            locked is None
            or locked.used_at is not None
            or locked.expires_at <= timezone.now()
        ):
            request.session.pop("caregiver_invite_id", None)
            request.session.pop("caregiver_invite_token_hash", None)
            messages.error(request, _("This sign-in link is invalid or has expired."))
            return redirect("caregiver_invite_redeem")
        caregiver = CaregiverProfile.create_from_invite(
            invite=locked,
            raw_pin=form.cleaned_data["pin"],
        )
        locked.used_at = timezone.now()
        locked.caregiver = caregiver
        locked.save(update_fields=["used_at", "caregiver"])
        login_code = caregiver.login_code

    request.session.pop("caregiver_invite_id", None)
    request.session.pop("caregiver_invite_token_hash", None)
    messages.success(request, _("Your guest PIN is ready. Sign in to continue."))
    return redirect("caregiver_login", login_code=login_code)


@never_cache
@require_http_methods(["GET", "POST"])
def caregiver_login(request, login_code):
    caregiver = (
        CaregiverProfile.objects.filter(login_code=login_code.upper())
        .select_related("user")
        .first()
    )
    if caregiver is None or not caregiver.has_access:
        messages.error(request, _("This guest access is no longer available."))
        return render(
            request,
            "economy/caregiver_login.html",
            {"form": None, "caregiver": None, "unavailable": True},
        )

    if request.method == "GET":
        return render(
            request,
            "economy/caregiver_login.html",
            {
                "form": CaregiverPinForm(),
                "caregiver": caregiver,
                "unavailable": False,
            },
        )

    if not register_attempt(
        AttemptCounter.Scope.CAREGIVER_PIN_IP,
        client_ip(request),
        window_seconds=300,
        limit=20,
    ) or not register_attempt(
        AttemptCounter.Scope.CAREGIVER_PIN_PROFILE,
        str(caregiver.pk),
        window_seconds=300,
        limit=10,
    ):
        messages.error(request, _("Too many PIN attempts. Try again later."))
        return render(
            request,
            "economy/caregiver_login.html",
            {
                "form": CaregiverPinForm(),
                "caregiver": caregiver,
                "unavailable": False,
            },
        )

    form = CaregiverPinForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "economy/caregiver_login.html",
            {"form": form, "caregiver": caregiver, "unavailable": False},
        )

    if caregiver.is_locked:
        messages.error(
            request,
            _("The profile is temporarily locked. Ask a parent to unlock it."),
        )
        return render(
            request,
            "economy/caregiver_login.html",
            {"form": CaregiverPinForm(), "caregiver": caregiver, "unavailable": False},
        )

    if not caregiver.verify_pin(form.cleaned_data["pin"]):
        if caregiver.is_locked:
            messages.error(
                request,
                _("Too many incorrect PINs. Ask a parent to unlock this access."),
            )
        else:
            messages.error(request, _("Incorrect PIN."))
        return render(
            request,
            "economy/caregiver_login.html",
            {"form": CaregiverPinForm(), "caregiver": caregiver, "unavailable": False},
        )

    reset_attempts(AttemptCounter.Scope.CAREGIVER_PIN_IP, client_ip(request))
    reset_attempts(AttemptCounter.Scope.CAREGIVER_PIN_PROFILE, str(caregiver.pk))
    logout(request)
    request.session.flush()
    login(request, caregiver.user, backend="django.contrib.auth.backends.ModelBackend")
    request.session.set_expiry(settings.PARENT_SESSION_SECONDS)
    return redirect("parent_dashboard")
