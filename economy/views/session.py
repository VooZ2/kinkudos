
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    logout,
)
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import (
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from economy.auth import current_device
from economy.email_config import smtp_config
from economy.forms import (
    ChildPinForm,
    ParentPasswordResetForm,
    ParentSetPasswordForm,
)
from economy.models import (
    AttemptCounter,
    ChildProfile,
    FamilySettings,
)
from economy.net import client_ip
from economy.rate_limit import register_attempt, reset_attempts


@method_decorator(never_cache, name="dispatch")
class ParentLoginView(LoginView):
    template_name = "economy/parent_login.html"
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username", "").strip().casefold()
        permitted = register_attempt(
            AttemptCounter.Scope.PARENT_LOGIN_IP,
            client_ip(request),
            window_seconds=300,
            limit=20,
        )
        if username:
            permitted = (
                register_attempt(
                    AttemptCounter.Scope.PARENT_LOGIN_ACCOUNT,
                    username,
                    window_seconds=300,
                    limit=10,
                )
                and permitted
            )
        if not permitted:
            form = self.get_form()
            form.add_error(None, _("Too many sign-in attempts. Try again later."))
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        reset_attempts(
            AttemptCounter.Scope.PARENT_LOGIN_IP,
            client_ip(self.request),
        )
        reset_attempts(
            AttemptCounter.Scope.PARENT_LOGIN_ACCOUNT,
            form.get_user().get_username().strip().casefold(),
        )
        self.request.session.flush()
        response = super().form_valid(form)
        self.request.session.set_expiry(settings.PARENT_SESSION_SECONDS)
        return response

class EmailResetEnabledMixin:
    def dispatch(self, request, *args, **kwargs):
        if not smtp_config().get("enabled"):
            raise Http404
        return super().dispatch(request, *args, **kwargs)

@method_decorator(never_cache, name="dispatch")
class ParentPasswordResetView(EmailResetEnabledMixin, PasswordResetView):
    template_name = "economy/password_reset_form.html"
    form_class = ParentPasswordResetForm
    email_template_name = "economy/password_reset_email.txt"
    subject_template_name = "economy/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email", "").strip().casefold()
        permitted = register_attempt(
            AttemptCounter.Scope.PASSWORD_RESET_IP,
            client_ip(request),
            window_seconds=900,
            limit=5,
        )
        if email:
            permitted = (
                register_attempt(
                    AttemptCounter.Scope.PASSWORD_RESET_ACCOUNT,
                    email,
                    window_seconds=900,
                    limit=3,
                )
                and permitted
            )
        if not permitted:
            form = self.get_form()
            form.add_error(None, _("Too many requests. Try again later."))
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.from_email = smtp_config().get("from_email")
        self.extra_email_context = {
            "family_display_name": FamilySettings.load().display_name,
        }
        return super().dispatch(request, *args, **kwargs)

@method_decorator(never_cache, name="dispatch")
class ParentPasswordResetDoneView(EmailResetEnabledMixin, PasswordResetDoneView):
    template_name = "economy/password_reset_done.html"

@method_decorator(never_cache, name="dispatch")
class ParentPasswordResetConfirmView(EmailResetEnabledMixin, PasswordResetConfirmView):
    template_name = "economy/password_reset_confirm.html"
    form_class = ParentSetPasswordForm
    success_url = reverse_lazy("password_reset_complete")

@method_decorator(never_cache, name="dispatch")
class ParentPasswordResetCompleteView(EmailResetEnabledMixin, PasswordResetCompleteView):
    template_name = "economy/password_reset_complete.html"

@never_cache
@require_POST
def session_logout(request):
    logout(request)
    request.session.flush()
    return redirect("home")

@never_cache
def child_select(request):
    device = current_device(request)
    if settings.DEVICE_PAIRING_REQUIRED and device is None:
        return render(request, "economy/device_not_paired.html")
    if request.method == "POST":
        form = ChildPinForm(request.POST)
        if form.is_valid():
            child = get_object_or_404(
                ChildProfile,
                pk=form.cleaned_data["child_id"],
                is_active=True,
            )
            device_key = str(device.pk) if device else f"dev:{client_ip(request)}"
            attempt_checks = (
                (
                    AttemptCounter.Scope.CHILD_PIN_DEVICE,
                    device_key,
                    300,
                    15,
                ),
                (
                    AttemptCounter.Scope.CHILD_PIN_PROFILE,
                    str(child.pk),
                    300,
                    10,
                ),
                (
                    AttemptCounter.Scope.CHILD_PIN_IP,
                    client_ip(request),
                    300,
                    30,
                ),
                (
                    AttemptCounter.Scope.CHILD_PIN_SITE,
                    "site",
                    300,
                    60,
                ),
            )
            attempts_allowed = all(
                register_attempt(
                    scope,
                    value,
                    window_seconds=seconds,
                    limit=limit,
                )
                for scope, value, seconds, limit in attempt_checks
            )
            if not attempts_allowed:
                messages.error(request, _("Too many PIN attempts. Try again later."))
            elif child.is_locked:
                messages.error(request, _("The profile is temporarily locked. Try again later."))
            elif child.verify_pin(form.cleaned_data["pin"]):
                reset_attempts(AttemptCounter.Scope.CHILD_PIN_DEVICE, device_key)
                reset_attempts(AttemptCounter.Scope.CHILD_PIN_PROFILE, str(child.pk))
                request.session.flush()
                request.session["child_id"] = child.pk
                if device:
                    request.session["child_device_id"] = device.pk
                request.session.set_expiry(settings.CHILD_SESSION_SECONDS)
                response = redirect("child_dashboard")
                response.set_cookie(
                    "kinkudos_last_child",
                    str(child.pk),
                    max_age=60 * 60 * 24 * 30,
                    httponly=True,
                    samesite="Lax",
                    secure=settings.SESSION_COOKIE_SECURE,
                )
                return response
            else:
                messages.error(request, _("Incorrect PIN."))
    else:
        form = ChildPinForm()
    return render(
        request,
        "economy/child_select.html",
        {
            "children": ChildProfile.objects.filter(is_active=True),
            "form": form,
            "last_child_id": request.COOKIES.get("kinkudos_last_child", ""),
        },
    )
