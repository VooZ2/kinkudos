import hashlib
import json
import logging
import smtplib
from datetime import date, datetime, time, timedelta
from urllib.parse import urlencode
from uuid import uuid4

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import check_password
from django.contrib.auth.views import (
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .auth import child_required, current_child, current_device, parent_required
from .backups import backup_status, configure_backup, request_manual_backup
from .changelog import load_changelog
from .email_config import public_smtp_config, save_smtp_config, smtp_config, verify_smtp
from .forms import (
    AdjustmentForm,
    ApplyPenaltyForm,
    ApprovalCostForm,
    AssignPenaltiesForm,
    AssignTasksForm,
    AvatarForm,
    AwardTasksForm,
    BackupSettingsForm,
    BirthDateForm,
    ChangePinForm,
    ChildAccountForm,
    ChildEditForm,
    ChildPinForm,
    FamilyPreferencesForm,
    FeedbackReportForm,
    FeedbackStatusForm,
    FirstThemeForm,
    GoalAmountForm,
    InitialSetupForm,
    MinBalanceForm,
    NetworkAccessForm,
    ParentAccountForm,
    ParentEditForm,
    ParentPasswordResetForm,
    ParentSetPasswordForm,
    PenaltyForm,
    PointGiftForm,
    ProposalForm,
    RejectForm,
    RewardForm,
    SavingsGoalForm,
    SmtpSettingsForm,
    TaskDecisionCommentForm,
    TaskEvidenceForm,
    TaskForm,
    ThemeForm,
)
from .images import (
    ImageProcessingError,
    process_avatar,
    process_feedback_screenshot,
    process_task_evidence,
)
from .lottery import (
    lottery_state,
    purchase_lottery_ticket,
    reveal_lottery_ticket,
)
from .models import (
    AssignedTask,
    AssignedTaskBatch,
    AssignedTaskStatus,
    AttemptCounter,
    BackupAuditEvent,
    BirthDateChangeRequest,
    ChildProfile,
    DevicePairingLink,
    DeviceToken,
    FamilySettings,
    FeedbackReport,
    FeedbackStatus,
    FeedbackType,
    GoalActivityType,
    GoalCompletionRequest,
    GoalMode,
    GoalStatus,
    LedgerEntry,
    LedgerKind,
    LotteryTicket,
    PenaltyTemplate,
    Proposal,
    ProposalType,
    PushSubscription,
    RequestStatus,
    Reward,
    RewardRequest,
    SavingsGoal,
    SavingsGoalEvent,
    SecurityAuditEvent,
    Task,
    TaskClaim,
    TaskCompletion,
)
from .net import client_ip
from .push import (
    notify_assigned_tasks,
    notify_birth_date_change,
    notify_birth_date_decision,
    notify_gift_received,
    notify_proposal,
    notify_proposal_decision,
    notify_reward_decision,
    notify_reward_request,
    notify_task_claim,
    notify_task_decision,
    notify_task_revision,
)
from .rate_limit import register_attempt, reset_attempts
from .services import (
    add_saved_points,
    approve_goal_completion,
    approve_proposal,
    approve_reward_request,
    approve_task_claim,
    assign_tasks,
    assigned_tasks_block_rewards,
    cancel_assigned_task,
    cancel_assigned_task_batch,
    close_savings_goal,
    complete_assigned_task,
    delete_savings_goal,
    keep_goal_active,
    post_ledger_entry,
    reject_task_claim,
    request_goal_completion,
    request_task_revision,
    resubmit_task_claim,
    return_saved_points,
    reward_is_affordable,
    reward_requests_blocked,
    select_goal_mode,
    submit_reward_request,
    submit_task,
    transfer_points,
    unavailable_assignment_task_ids,
    update_savings_goal,
)
from .setup import SetupUnavailable, complete_setup, setup_is_available, token_is_valid

logger = logging.getLogger(__name__)


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
        if form.is_valid():
            if not token_is_valid(form.cleaned_data["setup_token"]):
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


@parent_required
@require_POST
def parent_pair_device(request):
    label = request.POST.get("label", "").strip() or _("Child device")
    actor = request.user
    device, raw_token = DeviceToken.issue(created_by=actor, label=label)
    SecurityAuditEvent.objects.create(
        actor=actor,
        action=SecurityAuditEvent.Action.DEVICE_PAIRED,
        detail=device.label,
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
    return response


@parent_required
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
    return render(
        request,
        "economy/pairing_link_created.html",
        {
            "pairing_url": f"{pairing_url}#{raw_token}",
            "pairing_expires_at": link.expires_at,
        },
    )


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
            label=_("Child device"),
        )
        link.used_at = timezone.now()
        link.save(update_fields=["used_at"])
        SecurityAuditEvent.objects.create(
            actor=link.created_by,
            action=SecurityAuditEvent.Action.DEVICE_PAIRED,
            detail=device.label,
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
    return response


@parent_required
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
            detail=device.label,
        )
    messages.success(request, _("Device access revoked."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")


@parent_required
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


@child_required
def child_dashboard(request):
    child = request.child
    child.available_goal_balance = max(0, child.balance)
    today = timezone.localdate()
    active_assigned_tasks = (
        AssignedTask.objects.filter(
            batch__child=child,
            batch__assigned_on=today,
            status=AssignedTaskStatus.PENDING,
        )
        .select_related("batch", "task")
        .order_by("batch__created_at", "pk")
    )
    assigned_reward_block = assigned_tasks_block_rewards(child)
    child_lottery = lottery_state(child)
    rewards = list(Reward.objects.filter(is_active=True, is_deleted=False))
    for reward in rewards:
        reward.is_affordable = reward_is_affordable(child, reward)
        reward.missing_amount = max(reward.cost - (child.balance - child.min_balance), 0)
    goals = list(
        child.goals.filter(status=GoalStatus.ACTIVE).annotate(
            _saved_amount=Coalesce(
                Sum(
                    "contributions__amount",
                    filter=Q(contributions__state="active"),
                ),
                Value(0),
            )
        )
    )
    pending_goal_ids = set(
        GoalCompletionRequest.objects.filter(
            goal__child=child,
            status=RequestStatus.PENDING,
        ).values_list("goal_id", flat=True)
    )
    for goal in goals:
        goal.has_pending_completion = goal.pk in pending_goal_ids
    ledger_entries = list(child.ledger_entries.select_related("actor").all()[:5])
    task_claims_by_id = {
        claim.pk: claim
        for claim in child.task_claims.filter(
            pk__in=[
                entry.source_id
                for entry in ledger_entries
                if entry.kind == LedgerKind.TASK and entry.source_id
            ]
        ).select_related("decided_by", "task")
    }
    reward_requests_by_id = {
        reward_request.pk: reward_request
        for reward_request in child.reward_requests.filter(
            pk__in=[
                entry.source_id
                for entry in ledger_entries
                if entry.kind == LedgerKind.REWARD and entry.source_id
            ]
        ).select_related("decided_by", "reward")
    }
    assigned_tasks_by_id = {
        assigned_task.pk: assigned_task
        for assigned_task in AssignedTask.objects.filter(
            pk__in=[
                entry.source_id
                for entry in ledger_entries
                if entry.kind == LedgerKind.ASSIGNED_TASK and entry.source_id
            ],
            batch__child=child,
        ).select_related("task")
    }
    for entry in ledger_entries:
        entry.history_type = "ledger"
        entry.history_timestamp = entry.created_at
        entry.task_claim = (
            task_claims_by_id.get(entry.source_id)
            if entry.kind == LedgerKind.TASK
            else None
        )
        entry.reward_request = (
            reward_requests_by_id.get(entry.source_id)
            if entry.kind == LedgerKind.REWARD
            else None
        )
        entry.assigned_task_item = (
            assigned_tasks_by_id.get(entry.source_id)
            if entry.kind == LedgerKind.ASSIGNED_TASK
            else None
        )
    rejected_task_decisions = list(
        child.task_claims.filter(
            status=RequestStatus.REJECTED,
            decided_at__isnull=False,
        )
        .select_related("decided_by", "task")
        .order_by("-decided_at", "-pk")[:5]
    )
    for task_claim in rejected_task_decisions:
        task_claim.history_type = "task_decision"
        task_claim.history_timestamp = task_claim.decided_at
    rejected_reward_decisions = list(
        child.reward_requests.filter(
            status=RequestStatus.REJECTED,
            decided_at__isnull=False,
        )
        .select_related("decided_by", "reward")
        .order_by("-decided_at", "-pk")[:5]
    )
    for reward_request in rejected_reward_decisions:
        reward_request.history_type = "reward_decision"
        reward_request.history_timestamp = reward_request.decided_at
    goal_events = list(
        SavingsGoalEvent.objects.filter(goal__child=child)
        .select_related("goal", "actor")
        .order_by("-created_at", "-pk")[:5]
    )
    for event in goal_events:
        event.history_type = "goal_event"
        event.history_timestamp = event.created_at
    history_entries = sorted(
        [
            *ledger_entries,
            *rejected_task_decisions,
            *rejected_reward_decisions,
            *goal_events,
        ],
        key=lambda entry: (entry.history_timestamp, entry.pk),
        reverse=True,
    )[:5]
    pending_task_ids = set(
        child.task_claims.filter(
            status__in=[RequestStatus.PENDING, RequestStatus.NEEDS_CHANGES]
        ).values_list("task_id", flat=True)
    )
    pending_reward_ids = set(
        child.reward_requests.filter(status=RequestStatus.PENDING).values_list(
            "reward_id", flat=True
        )
    )
    return render(
        request,
        "economy/child_dashboard.html",
        {
            "child": child,
            "tasks": Task.objects.filter(is_active=True, is_deleted=False),
            "rewards": rewards,
            "pending_task_ids": pending_task_ids,
            "pending_reward_ids": pending_reward_ids,
            "pending_requests": child.reward_requests.filter(status=RequestStatus.PENDING),
            "revision_claims": child.task_claims.filter(
                status=RequestStatus.NEEDS_CHANGES
            ).select_related("task"),
            "rejected_task_claims": child.task_claims.filter(
                status=RequestStatus.REJECTED,
                child_acknowledged_at__isnull=True,
            )
            .select_related("task", "decided_by")
            .order_by("-decided_at")[:5],
            "goals": goals,
            "ledger": history_entries,
            "active_assigned_tasks": active_assigned_tasks,
            "assigned_tasks_block_rewards": assigned_reward_block,
            "credit_reward_requests_blocked": reward_requests_blocked(child),
            "reward_requests_blocked": (
                assigned_reward_block or reward_requests_blocked(child)
            ),
            "lottery": child_lottery,
            "proposal_form": ProposalForm(),
            "task_evidence_form": TaskEvidenceForm(),
            "theme_form": ThemeForm(
                initial={
                    "theme": child.theme,
                    "randomize_theme_daily": child.randomize_theme_daily,
                }
            ),
            "change_pin_form": ChangePinForm(),
            "avatar_form": AvatarForm(),
            "birth_date_form": BirthDateForm(instance=child),
            "pending_birth_date_request": child.birth_date_change_requests.filter(
                status=RequestStatus.PENDING
            ).first(),
            "child_state_signature": _child_state_signature(child),
            "gift_form": PointGiftForm(sender=child),
            "gift_recipients_available": ChildProfile.objects.filter(
                is_active=True
            ).exclude(pk=child.pk).exists(),
        },
    )


@never_cache
@child_required
def child_theme_onboarding(request):
    form = FirstThemeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        request.child.theme = form.cleaned_data["theme"]
        request.child.theme_selected = True
        request.child.save(update_fields=["theme", "theme_selected"])
        messages.success(request, _("Your world is ready."))
        return redirect("child_dashboard")
    return render(
        request,
        "economy/child_theme_onboarding.html",
        {"child": request.child, "form": form},
    )


def _child_action_response(request, *, ok, effect=None):
    """Return JSON to enhanced child forms and preserve redirects as a fallback."""
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        payload = {
            "ok": ok,
            "redirect_url": reverse("child_dashboard"),
        }
        if effect:
            payload["effect"] = effect
        return JsonResponse(payload, status=200 if ok else 400)
    return redirect("child_dashboard")


@child_required
@require_POST
def child_submit_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id, is_active=True)
    form = TaskEvidenceForm(request.POST, request.FILES)
    if not form.is_valid():
        error = next(iter(form.errors.values()))[0]
        messages.error(request, str(error))
        return _child_action_response(request, ok=False)

    upload = form.cleaned_data.get("proof")
    processed = None
    if upload:
        try:
            processed = process_task_evidence(upload)
        except ImageProcessingError:
            messages.error(
                request,
                _("The image could not be processed. Choose another file."),
            )
            return _child_action_response(request, ok=False)

    submitted = False
    try:
        bonus = FamilySettings.load().photo_bonus_points if processed else 0
        claim = submit_task(
            child=request.child,
            task=task,
            photo_bonus_snapshot=bonus,
        )
        if processed:
            _replace_task_evidence(claim, processed)
        notify_task_claim(claim)
        if request.child.theme == "block_world":
            success_message = _("Block sent to your parents for approval.")
        elif request.child.theme == "magic_academy":
            success_message = _("The owl carried your task to your parents.")
        elif request.child.theme == "hero_hq":
            success_message = _(
                "Signal received! Mission evidence was delivered to HQ."
            )
        elif request.child.theme == "art_studio":
            success_message = _("Your artwork was sent to the review gallery!")
        elif request.child.theme == "panda_pet":
            success_message = _("The bamboo was sent to your parents for approval!")
        elif request.child.theme == "blockville":
            success_message = _("Challenge complete! Pending parent verification.")
        elif processed:
            success_message = _("The task and its proof were sent to the parents for approval.")
        else:
            success_message = _("The task was sent to the parents for approval.")
        messages.success(request, success_message, extra_tags="task-success")
        submitted = True
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return _child_action_response(
        request,
        ok=submitted,
        effect="task" if submitted else None,
    )


@child_required
@require_POST
def child_resubmit_task(request, claim_id):
    claim = get_object_or_404(
        TaskClaim,
        pk=claim_id,
        child=request.child,
        status=RequestStatus.NEEDS_CHANGES,
    )
    form = TaskEvidenceForm(request.POST, request.FILES)
    if not form.is_valid():
        error = next(iter(form.errors.values()))[0]
        messages.error(request, str(error))
        return _child_action_response(request, ok=False)

    upload = form.cleaned_data.get("proof")
    submitted = False
    try:
        if form.cleaned_data.get("remove_evidence"):
            _delete_task_evidence(claim)
            claim.photo_bonus_snapshot = 0
            claim.save(update_fields=["photo_bonus_snapshot"])
        if upload:
            processed = process_task_evidence(upload)
            _replace_task_evidence(claim, processed)
            claim.photo_bonus_snapshot = FamilySettings.load().photo_bonus_points
            claim.save(update_fields=["photo_bonus_snapshot"])
        resubmit_task_claim(claim=claim)
        claim.refresh_from_db()
        notify_task_claim(claim)
        messages.success(
            request,
            _("The corrected task was sent for approval again."),
            extra_tags="task-success",
        )
        submitted = True
    except ImageProcessingError:
        messages.error(request, _("The image could not be processed. Choose another file."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return _child_action_response(
        request,
        ok=submitted,
        effect="task" if submitted else None,
    )


@child_required
@require_POST
def child_acknowledge_task_response(request, claim_id):
    claim = get_object_or_404(
        TaskClaim,
        pk=claim_id,
        child=request.child,
        status=RequestStatus.REJECTED,
    )
    if claim.child_acknowledged_at is None:
        claim.child_acknowledged_at = timezone.now()
        claim.save(update_fields=["child_acknowledged_at"])
    return redirect("child_dashboard")


@child_required
@require_POST
def child_request_reward(request, reward_id):
    reward = get_object_or_404(Reward, pk=reward_id, is_active=True)
    submitted = False
    try:
        reward_request = submit_reward_request(child=request.child, reward=reward)
        notify_reward_request(reward_request)
        messages.success(
            request,
            _("The reward request was sent to the parents."),
            extra_tags="reward-success",
        )
        submitted = True
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return _child_action_response(
        request,
        ok=submitted,
        effect="reward" if submitted else None,
    )


@child_required
@require_POST
def child_purchase_lottery_ticket(request):
    try:
        purchase_lottery_ticket(child=request.child)
        messages.success(request, _("Your scratch ticket is ready."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('child_dashboard')}#prizai")


@child_required
@require_POST
def child_reveal_lottery_ticket(request, ticket_id):
    ticket = get_object_or_404(
        LotteryTicket,
        pk=ticket_id,
        child=request.child,
    )
    revealed = reveal_lottery_ticket(ticket=ticket, child=request.child)
    revealed.refresh_from_db()
    return JsonResponse(
        {
            "ok": True,
            "delta": revealed.applied_delta,
            "balance": revealed.result_ledger_entry.balance_after,
            "matching_value": revealed.prize_amount,
        }
    )


@child_required
@require_POST
def child_cancel_reward(request, request_id):
    reward_request = get_object_or_404(
        RewardRequest,
        pk=request_id,
        child=request.child,
        status=RequestStatus.PENDING,
    )
    reward_request.status = RequestStatus.CANCELLED
    reward_request.decided_at = timezone.now()
    reward_request.save(update_fields=["status", "decided_at"])
    messages.success(request, _("The reward request was cancelled."))
    return redirect("child_dashboard")


@child_required
@require_POST
def child_create_proposal(request):
    form = ProposalForm(request.POST)
    if form.is_valid():
        proposal = form.save(commit=False)
        proposal.child = request.child
        proposal.save()
        notify_proposal(proposal)
        messages.success(request, _("The suggestion was sent to the parents."))
    else:
        messages.error(request, _("Check the suggestion details."))
    return redirect("child_dashboard")


@child_required
@require_POST
def child_set_goal_mode(request, goal_id):
    goal = get_object_or_404(
        SavingsGoal,
        pk=goal_id,
        child=request.child,
        status=GoalStatus.ACTIVE,
    )
    try:
        select_goal_mode(
            goal=goal,
            child=request.child,
            mode=request.POST.get("mode", ""),
        )
        messages.success(request, _("Savings mode saved."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('child_dashboard')}#tikslai")


@child_required
@require_POST
def child_add_goal_points(request, goal_id):
    goal = get_object_or_404(
        SavingsGoal,
        pk=goal_id,
        child=request.child,
        status=GoalStatus.ACTIVE,
    )
    form = GoalAmountForm(request.POST)
    try:
        if not form.is_valid():
            raise ValidationError(_("Enter a valid point amount."))
        add_saved_points(
            goal=goal,
            child=request.child,
            amount=form.cleaned_data["amount"],
        )
        messages.success(request, _("Points were saved for this goal."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('child_dashboard')}#tikslai")


@child_required
@require_POST
def child_request_goal_completion(request, goal_id):
    goal = get_object_or_404(
        SavingsGoal,
        pk=goal_id,
        child=request.child,
        status=GoalStatus.ACTIVE,
    )
    try:
        request_goal_completion(goal=goal, child=request.child)
        messages.success(request, _("The goal was sent to the parents for approval."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('child_dashboard')}#tikslai")


@child_required
@require_POST
def child_set_theme(request):
    form = ThemeForm(request.POST)
    if form.is_valid():
        request.child.theme = form.cleaned_data["theme"]
        request.child.theme_selected = True
        request.child.randomize_theme_daily = form.cleaned_data[
            "randomize_theme_daily"
        ]
        request.child.save(
            update_fields=["theme", "theme_selected", "randomize_theme_daily"]
        )
        messages.success(request, _("Theme changed."))
    return redirect("child_dashboard")


@child_required
@require_POST
def child_set_birth_date(request):
    child = request.child
    current_birth_date = child.birth_date
    birth_date_initialized = child.birth_date_initialized
    form = BirthDateForm(request.POST, instance=child)
    if form.is_valid():
        requested_birth_date = form.cleaned_data["birth_date"]
        if not birth_date_initialized:
            if requested_birth_date is None:
                messages.error(request, _("Enter the birthday date."))
            else:
                child.birth_date = requested_birth_date
                child.birth_date_initialized = True
                child.save(update_fields=["birth_date", "birth_date_initialized"])
                messages.success(request, _("Birthday saved."))
        elif requested_birth_date == current_birth_date:
            messages.info(request, _("The birthday date has not changed."))
        elif child.birth_date_change_requests.filter(
            status=RequestStatus.PENDING
        ).exists():
            messages.error(
                request,
                _("A birthday change is already waiting for parent approval."),
            )
        else:
            change = BirthDateChangeRequest.objects.create(
                child=child,
                previous_birth_date=current_birth_date,
                requested_birth_date=requested_birth_date,
            )
            notify_birth_date_change(change)
            messages.success(
                request,
                _("The birthday change was sent to the parents for approval."),
            )
    else:
        messages.error(request, _("Check the birthday date."))
    return redirect("child_dashboard")


def _child_state_payload(child):
    latest_ledger = child.ledger_entries.order_by("-pk").values_list(
        "pk", "created_at"
    ).first()
    task_states = list(
        child.task_claims.order_by("-submitted_at", "-pk")
        .values_list("pk", "status", "submitted_at", "decided_at")[:20]
    )
    reward_states = list(
        child.reward_requests.order_by("-submitted_at", "-pk")
        .values_list("pk", "status", "submitted_at", "decided_at")[:20]
    )
    assigned_task_states = list(
        AssignedTask.objects.filter(batch__child=child)
        .order_by("-batch__created_at", "-pk")
        .values_list("pk", "status", "batch__assigned_on", "completed_at")[:20]
    )
    lottery_states = list(
        child.lottery_tickets.order_by("-purchased_at", "-pk").values_list(
            "pk",
            "status",
            "week_start",
            "purchased_at",
            "revealed_at",
        )[:12]
    )
    goal_states = list(
        child.goals.order_by("-created_at", "-pk").values_list(
            "pk", "mode", "status", "target_amount"
        )
    )
    raw_state = json.dumps(
        {
            "local_date": timezone.localdate(),
            "balance": child.balance,
            "ledger": latest_ledger,
            "tasks": task_states,
            "rewards": reward_states,
            "assigned_tasks": assigned_task_states,
            "lottery": lottery_states,
            "goals": goal_states,
        },
        default=str,
        sort_keys=True,
    )
    return {
        "balance": child.balance,
        "signature": hashlib.sha256(raw_state.encode("utf-8")).hexdigest(),
    }


def _child_state_signature(child):
    return _child_state_payload(child)["signature"]


@child_required
def child_state(request):
    response = JsonResponse(_child_state_payload(request.child))
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    return response


@child_required
@require_POST
def child_give_points(request):
    form = PointGiftForm(request.POST, sender=request.child)
    if not form.is_valid():
        error = next(iter(form.errors.values()))[0]
        messages.error(request, str(error))
        return redirect("child_dashboard")
    try:
        gift = transfer_points(
            sender=request.child,
            recipient=form.cleaned_data["recipient"],
            amount=form.cleaned_data["amount"],
        )
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    else:
        notify_gift_received(gift)
        messages.success(request, _("Your point gift was sent."))
    return redirect("child_dashboard")


@child_required
@require_POST
def child_change_pin(request):
    form = ChangePinForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Check the PIN fields."))
        return redirect("child_dashboard")
    if not check_password(form.cleaned_data["current_pin"], request.child.pin_hash):
        messages.error(request, _("The current PIN is incorrect."))
        return redirect("child_dashboard")
    request.child.set_pin(form.cleaned_data["new_pin"])
    request.child.failed_pin_attempts = 0
    request.child.locked_until = None
    request.child.save(update_fields=["pin_hash", "failed_pin_attempts", "locked_until"])
    messages.success(request, _("PIN changed."))
    return redirect("child_dashboard")


@child_required
@require_POST
def child_set_avatar(request):
    form = AvatarForm(request.POST, request.FILES)
    if not form.is_valid():
        error = next(iter(form.errors.values()))[0]
        messages.error(request, str(error))
        return redirect("child_dashboard")

    upload = form.cleaned_data["avatar"]
    try:
        avatar_bytes = process_avatar(upload)
    except ImageProcessingError:
        messages.error(request, _("The image could not be processed. Choose another file."))
        return redirect("child_dashboard")

    child = request.child
    old_name = child.avatar.name
    file_name = f"{slugify(child.name) or 'vaikas'}-{uuid4().hex}.webp"
    child.avatar.save(file_name, ContentFile(avatar_bytes), save=False)
    child.save(update_fields=["avatar"])
    if old_name:
        child.avatar.storage.delete(old_name)
    messages.success(request, _("Avatar changed."))
    return redirect("child_dashboard")


def _delete_task_evidence(claim, *, mark_purged=False):
    names = [
        (claim.evidence_image.storage, claim.evidence_image.name)
        if claim.evidence_image
        else None,
        (claim.evidence_thumbnail.storage, claim.evidence_thumbnail.name)
        if claim.evidence_thumbnail
        else None,
    ]
    claim.evidence_image = ""
    claim.evidence_thumbnail = ""
    if mark_purged:
        claim.evidence_purged_at = timezone.now()
    claim.save(
        update_fields=[
            "evidence_image",
            "evidence_thumbnail",
            *(["evidence_purged_at"] if mark_purged else []),
        ]
    )
    for item in names:
        if item:
            storage, name = item
            storage.delete(name)


def _replace_task_evidence(claim, processed):
    old_names = [
        (claim.evidence_image.storage, claim.evidence_image.name)
        if claim.evidence_image
        else None,
        (claim.evidence_thumbnail.storage, claim.evidence_thumbnail.name)
        if claim.evidence_thumbnail
        else None,
    ]
    identifier = uuid4().hex
    claim.evidence_image.save(
        f"{identifier}.webp",
        ContentFile(processed.image),
        save=False,
    )
    claim.evidence_thumbnail.save(
        f"{identifier}-thumb.webp",
        ContentFile(processed.thumbnail),
        save=False,
    )
    claim.evidence_uploaded_at = timezone.now()
    claim.evidence_purged_at = None
    claim.save(
        update_fields=[
            "evidence_image",
            "evidence_thumbnail",
            "evidence_uploaded_at",
            "evidence_purged_at",
        ]
    )
    for item in old_names:
        if item:
            storage, name = item
            storage.delete(name)


def child_avatar(request, child_id):
    if (
        not request.user.is_authenticated
        and settings.DEVICE_PAIRING_REQUIRED
        and current_device(request) is None
    ):
        raise Http404
    child = get_object_or_404(ChildProfile, pk=child_id, is_active=True)
    if not child.avatar:
        raise Http404
    response = FileResponse(child.avatar.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "private, max-age=300"
    response["X-Content-Type-Options"] = "nosniff"
    return response


def task_evidence(request, claim_id, size):
    claim = get_object_or_404(TaskClaim.objects.select_related("child"), pk=claim_id)
    child = current_child(request)
    if not request.user.is_authenticated and (child is None or child.pk != claim.child_id):
        raise Http404
    field = claim.evidence_thumbnail if size == "thumbnail" else claim.evidence_image
    if size not in {"thumbnail", "full"} or not field:
        raise Http404
    response = FileResponse(field.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "private, max-age=300"
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = "inline"
    return response


def _feedback_actor(request):
    if request.user.is_authenticated:
        return request.user, None
    return None, current_child(request)


def _feedback_redirect(request):
    target = request.POST.get("next", "")
    if (
        target
        and target.startswith("/")
        and url_has_allowed_host_and_scheme(
            target,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
    ):
        return target
    return reverse("home")


@require_POST
def submit_feedback(request):
    parent, child = _feedback_actor(request)
    if parent is None and child is None:
        raise Http404

    recent_reports = FeedbackReport.objects.filter(
        created_at__gte=timezone.now() - timedelta(minutes=1)
    )
    recent_reports = (
        recent_reports.filter(parent=parent)
        if parent is not None
        else recent_reports.filter(child=child)
    )
    if recent_reports.count() >= 3:
        messages.error(
            request,
            _("Too many reports were sent. Wait a minute and try again."),
        )
        return redirect(_feedback_redirect(request))

    form = FeedbackReportForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(
            request,
            _("Check the feedback description and screenshot."),
        )
        return redirect(_feedback_redirect(request))

    screenshot = form.cleaned_data.get("screenshot")
    screenshot_bytes = None
    if screenshot:
        try:
            screenshot_bytes = process_feedback_screenshot(screenshot)
        except ImageProcessingError:
            messages.error(
                request,
                _("The image could not be processed. Choose another file."),
            )
            return redirect(_feedback_redirect(request))

    family = FamilySettings.load()
    report = form.save(commit=False)
    report.parent = parent
    report.child = child
    report.reporter_name = parent.username if parent is not None else child.name
    report.reporter_role = "parent" if parent is not None else "child"
    report.family_name = family.family_name
    page_path = request.POST.get("page_path", "")
    report.page_path = (
        page_path.split("?", 1)[0].split("#", 1)[0][:500]
        if page_path.startswith("/")
        else ""
    )
    report.app_version = settings.APP_VERSION
    report.language = request.LANGUAGE_CODE[:16]
    report.theme = child.theme if child is not None else ""
    report.user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
    report.save()
    if screenshot_bytes:
        report.screenshot.save(
            f"{uuid4().hex}.webp",
            ContentFile(screenshot_bytes),
            save=True,
        )

    email_failed = False
    email = smtp_config()
    if email.get("enabled") and email.get("feedback_email"):
        try:
            parent_url = request.build_absolute_uri(
                f"{reverse('parent_dashboard')}#parent-settings"
            )
            send_mail(
                _(
                    "KinKudos feedback #%(report_id)s: %(report_type)s"
                )
                % {
                    "report_id": report.pk,
                    "report_type": report.get_report_type_display(),
                },
                "\n".join(
                    [
                        f"ID: {report.pk}",
                        f"Type: {report.get_report_type_display()}",
                        f"Reporter: {report.reporter_name} ({report.reporter_role})",
                        f"Family: {report.family_name}",
                        f"Version: {report.app_version}",
                        f"Page: {report.page_path}",
                        f"Language: {report.language}",
                        f"Theme: {report.theme or '-'}",
                        "",
                        report.description,
                        "",
                        f"Review: {parent_url}",
                    ]
                ),
                email.get("from_email"),
                [email.get("feedback_email")],
                fail_silently=False,
            )
            report.email_notified_at = timezone.now()
            report.email_error = ""
            report.save(update_fields=["email_notified_at", "email_error"])
        except Exception as exc:  # SMTP failures must not lose the saved report.
            logger.warning("Feedback email notification failed", exc_info=True)
            report.email_error = type(exc).__name__[:240]
            report.save(update_fields=["email_error"])
            email_failed = True

    if email_failed:
        messages.warning(
            request,
            _("Feedback was saved, but the email notification could not be sent."),
        )
    else:
        messages.success(request, _("Thank you. Your feedback was sent."))
    return redirect(_feedback_redirect(request))


def feedback_screenshot(request, report_id):
    report = get_object_or_404(FeedbackReport, pk=report_id)
    child = current_child(request)
    if not request.user.is_authenticated and (
        child is None or report.child_id != child.pk
    ):
        raise Http404
    if not report.screenshot:
        raise Http404
    response = FileResponse(report.screenshot.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "private, max-age=300"
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = "inline"
    return response


@parent_required
@require_POST
def parent_update_feedback_status(request, report_id):
    report = get_object_or_404(FeedbackReport, pk=report_id)
    form = FeedbackStatusForm(request.POST)
    if form.is_valid():
        report.status = form.cleaned_data["status"]
        report.save(update_fields=["status", "updated_at"])
        messages.success(request, _("Feedback status updated."))
    else:
        messages.error(request, _("Choose a valid feedback status."))
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")


def _pending_request_items(goals_by_child):
    pending_requests = []
    pending_claims = list(
        TaskClaim.objects.filter(
            status=RequestStatus.PENDING,
            child__is_active=True,
        )
        .select_related("child", "task")
        .order_by("submitted_at", "pk")
    )
    pending_rewards = list(
        RewardRequest.objects.filter(
            status=RequestStatus.PENDING,
            child__is_active=True,
        )
        .select_related("child", "reward")
        .order_by("submitted_at", "pk")
    )
    pending_proposals = list(
        Proposal.objects.filter(
            status=RequestStatus.PENDING,
            child__is_active=True,
        )
        .select_related("child")
        .order_by("created_at", "pk")
    )
    for proposal in pending_proposals:
        proposal.replaces_current_goal = bool(
            proposal.proposal_type == ProposalType.GOAL
            and proposal.goal_mode == GoalMode.AVAILABLE
            and any(
                goal.status == GoalStatus.ACTIVE and goal.mode == GoalMode.AVAILABLE
                for goal in goals_by_child.get(proposal.child_id, [])
            )
        )
    pending_goal_completions = list(
        GoalCompletionRequest.objects.filter(
            status=RequestStatus.PENDING,
            goal__child__is_active=True,
        )
        .select_related("goal", "goal__child")
        .order_by("requested_at", "pk")
    )
    pending_birth_date_changes = list(
        BirthDateChangeRequest.objects.filter(
            status=RequestStatus.PENDING,
            child__is_active=True,
        )
        .select_related("child")
        .order_by("requested_at", "pk")
    )
    for claim in pending_claims:
        pending_requests.append(
            {
                "kind": "task",
                "child": claim.child,
                "claim": claim,
                "submitted_at": claim.submitted_at,
            }
        )
    for reward_request in pending_rewards:
        pending_requests.append(
            {
                "kind": "reward",
                "child": reward_request.child,
                "reward_request": reward_request,
                "submitted_at": reward_request.submitted_at,
            }
        )
    for proposal in pending_proposals:
        pending_requests.append(
            {
                "kind": "proposal",
                "child": proposal.child,
                "proposal": proposal,
                "submitted_at": proposal.created_at,
            }
        )
    for completion in pending_goal_completions:
        pending_requests.append(
            {
                "kind": "goal",
                "child": completion.goal.child,
                "completion": completion,
                "submitted_at": completion.requested_at,
            }
        )
    for change in pending_birth_date_changes:
        pending_requests.append(
            {
                "kind": "birthday",
                "child": change.child,
                "change": change,
                "submitted_at": change.requested_at,
            }
        )
    pending_requests.sort(
        key=lambda item: (item["submitted_at"], item["kind"]),
    )
    return pending_requests


@parent_required
def parent_pending_requests(request):
    children = list(ChildProfile.objects.filter(is_active=True))
    goals = list(
        SavingsGoal.objects.filter(child__is_active=True)
        .select_related("child")
    )
    goals_by_child = {child.pk: [] for child in children}
    for goal in goals:
        goals_by_child.setdefault(goal.child_id, []).append(goal)
    pending_requests = _pending_request_items(goals_by_child)
    return render(
        request,
        "economy/includes/pending_requests.html",
        {
            "pending_requests": pending_requests,
            "pending_count": len(pending_requests),
            "pending_requests_fragment": True,
        },
    )


@parent_required
def parent_dashboard(request):
    children = list(ChildProfile.objects.filter(is_active=True))
    today = timezone.localdate()
    history_date = request.GET.get("history_date", "any").strip()
    history_custom_start = request.GET.get("history_start", "").strip()
    history_custom_end = request.GET.get("history_end", "").strip()
    history_date_error = ""
    if (history_custom_start or history_custom_end) and history_date != "custom":
        history_date = "custom"
    history_cutoff = None
    history_end_at = None
    if history_date == "week":
        history_cutoff = timezone.now() - timedelta(days=7)
    elif history_date == "month":
        history_cutoff = timezone.now() - timedelta(days=30)
    elif history_date == "custom":
        try:
            start = date.fromisoformat(history_custom_start) if history_custom_start else None
            end = date.fromisoformat(history_custom_end) if history_custom_end else None
            if start and end and start > end:
                history_date_error = _("From date must not be later than To date.")
            if start and not history_date_error:
                history_cutoff = timezone.make_aware(datetime.combine(start, time.min))
            if end and not history_date_error:
                history_end_at = timezone.make_aware(datetime.combine(end, time.max))
        except ValueError:
            history_date_error = _("Enter a valid date range.")
    elif history_date != "any":
        history_date = "any"
        history_custom_start = ""
        history_custom_end = ""
    all_goals = list(
        SavingsGoal.objects.filter(child__is_active=True)
        .select_related("child")
        .annotate(
            _saved_amount=Coalesce(
                Sum(
                    "contributions__amount",
                    filter=Q(contributions__state="active"),
                ),
                Value(0),
            )
        )
    )
    pending_goal_completions = list(
        GoalCompletionRequest.objects.filter(
            status=RequestStatus.PENDING,
            goal__child__is_active=True,
        ).select_related("goal", "goal__child")
    )
    pending_goal_ids = {item.goal_id for item in pending_goal_completions}
    goals_by_child = {child.pk: [] for child in children}
    for goal in all_goals:
        goal.has_pending_completion = goal.pk in pending_goal_ids
        goals_by_child.setdefault(goal.child_id, []).append(goal)
    for child in children:
        child.dashboard_goals = [
            goal
            for goal in goals_by_child.get(child.pk, [])
            if goal.status == GoalStatus.ACTIVE
        ]
        child.saved_total = sum(goal.saved_amount for goal in child.dashboard_goals)
        child.goal_summary = None
        if child.dashboard_goals:
            child.goal_summary = next(
                (
                    goal
                    for goal in child.dashboard_goals
                    if goal.has_pending_completion and goal.is_reached
                ),
                None,
            )
            if child.goal_summary is None:
                child.goal_summary = next(
                    (
                        goal
                        for goal in child.dashboard_goals
                        if goal.mode == GoalMode.AVAILABLE
                    ),
                    None,
                )
            if child.goal_summary is None:
                saved_goals = [
                    goal
                    for goal in child.dashboard_goals
                    if goal.mode == GoalMode.SAVED
                ]
                child.goal_summary = min(
                    saved_goals or child.dashboard_goals,
                    key=lambda goal: goal.target_amount - goal.saved_amount,
                )
            child.additional_goal_count = max(len(child.dashboard_goals) - 1, 0)
    for child in children:
        child_lottery = lottery_state(child)
        child.lottery_tickets_used = child_lottery["tickets_used"]
        child.lottery_tickets_remaining = child_lottery["tickets_remaining"]
        child.lottery_ticket_open = bool(child_lottery["open_ticket"])
        child.lottery_feature_enabled = child_lottery["feature_enabled"]
        child.lottery_weekly_limit = child_lottery["weekly_limit"]
        child.assignment_unavailable_task_ids = unavailable_assignment_task_ids(child)
        child.assignment_batches = list(
            child.assigned_task_batches.filter(assigned_on__lte=today)
            .select_related("assigned_by")
            .prefetch_related("items__task", "items__cancelled_by")[:10]
        )
        for batch in child.assignment_batches:
            batch.has_pending_items = batch.assigned_on == today and any(
                item.status == AssignedTaskStatus.PENDING
                for item in batch.items.all()
            )
    history_children = list(ChildProfile.objects.order_by("name"))
    feedback_status = request.GET.get("feedback_status", "active").strip()
    feedback_type = request.GET.get("feedback_type", "").strip()
    feedback_query = FeedbackReport.objects.select_related("parent", "child")
    if feedback_status == "active":
        feedback_query = feedback_query.exclude(status=FeedbackStatus.RESOLVED)
    elif feedback_status in FeedbackStatus.values:
        feedback_query = feedback_query.filter(status=feedback_status)
    else:
        feedback_status = ""
    if feedback_type in FeedbackType.values:
        feedback_query = feedback_query.filter(report_type=feedback_type)
    else:
        feedback_type = ""
    feedback_page = Paginator(feedback_query, 20).get_page(
        request.GET.get("feedback_page", 1)
    )
    history_child_id = request.GET.get("history_child", "").strip()
    history_activity = request.GET.get("history_activity", "").strip()
    ledger_query = LedgerEntry.objects.all().select_related("child", "actor")
    if history_cutoff is not None:
        ledger_query = ledger_query.filter(created_at__gte=history_cutoff)
    if history_end_at is not None:
        ledger_query = ledger_query.filter(created_at__lte=history_end_at)
    reward_decisions = RewardRequest.objects.filter(
        status__in=[RequestStatus.APPROVED, RequestStatus.REJECTED],
        decided_at__isnull=False,
    ).select_related("child", "decided_by")
    if history_cutoff is not None:
        reward_decisions = reward_decisions.filter(decided_at__gte=history_cutoff)
    if history_end_at is not None:
        reward_decisions = reward_decisions.filter(decided_at__lte=history_end_at)
    task_decisions = TaskClaim.objects.filter(
        status=RequestStatus.REJECTED,
        decided_at__isnull=False,
    ).select_related("child", "decided_by", "task")
    if history_cutoff is not None:
        task_decisions = task_decisions.filter(decided_at__gte=history_cutoff)
    if history_end_at is not None:
        task_decisions = task_decisions.filter(decided_at__lte=history_end_at)
    proposal_decisions = Proposal.objects.filter(
        status__in=[RequestStatus.APPROVED, RequestStatus.REJECTED],
        decided_at__isnull=False,
    ).select_related("child", "decided_by")
    if history_cutoff is not None:
        proposal_decisions = proposal_decisions.filter(decided_at__gte=history_cutoff)
    if history_end_at is not None:
        proposal_decisions = proposal_decisions.filter(decided_at__lte=history_end_at)
    goal_events_query = SavingsGoalEvent.objects.filter(
        goal__child__is_active=True,
    ).select_related("goal", "goal__child", "actor")
    if history_cutoff is not None:
        goal_events_query = goal_events_query.filter(created_at__gte=history_cutoff)
    if history_end_at is not None:
        goal_events_query = goal_events_query.filter(created_at__lte=history_end_at)
    activity_kinds = {
        "tasks": [LedgerKind.TASK, LedgerKind.ASSIGNED_TASK],
        "penalties": [LedgerKind.PENALTY],
        "rewards": [LedgerKind.REWARD],
        "gifts": [LedgerKind.GIFT],
        "scratch": [LedgerKind.LOTTERY],
        "adjustments": [LedgerKind.ADJUSTMENT, LedgerKind.BIRTHDAY],
        "goals": [
            LedgerKind.SAVINGS_TRANSFER,
            LedgerKind.SAVINGS_RETURN,
            LedgerKind.GOAL_COMPLETION,
        ],
    }
    if history_activity in activity_kinds:
        ledger_query = ledger_query.filter(kind__in=activity_kinds[history_activity])
        if history_activity != "goals":
            goal_events_query = goal_events_query.none()
        if history_activity != "rewards":
            reward_decisions = reward_decisions.none()
        if history_activity != "tasks":
            task_decisions = task_decisions.none()
        if history_activity == "goals":
            proposal_decisions = proposal_decisions.filter(proposal_type=ProposalType.GOAL)
        elif history_activity == "rewards":
            proposal_decisions = proposal_decisions.filter(proposal_type=ProposalType.REWARD)
        else:
            proposal_decisions = proposal_decisions.none()
    elif history_activity:
        history_activity = ""
    if history_child_id.isdigit() and any(
        child.pk == int(history_child_id) for child in history_children
    ):
        ledger_query = ledger_query.filter(child_id=int(history_child_id))
        reward_decisions = reward_decisions.filter(child_id=int(history_child_id))
        task_decisions = task_decisions.filter(child_id=int(history_child_id))
        proposal_decisions = proposal_decisions.filter(child_id=int(history_child_id))
        goal_events_query = goal_events_query.filter(
            goal__child_id=int(history_child_id)
        )
    else:
        history_child_id = ""
    ledger_entries = list(ledger_query.order_by("-created_at", "-pk")[:50])
    reward_decisions = list(reward_decisions.order_by("-decided_at", "-pk")[:50])
    reward_decisions_by_id = {
        reward_request.pk: reward_request
        for reward_request in reward_decisions
    }
    for entry in ledger_entries:
        entry.history_type = "ledger"
        entry.reward_request = (
            reward_decisions_by_id.get(entry.source_id)
            if entry.kind == LedgerKind.REWARD and entry.source_id
            else None
        )
        entry.history_timestamp = entry.created_at
    rejected_reward_decisions = []
    for reward_request in reward_decisions:
        if reward_request.status != RequestStatus.REJECTED:
            continue
        reward_request.history_type = "reward_decision"
        reward_request.history_timestamp = reward_request.decided_at
        rejected_reward_decisions.append(reward_request)
    rejected_task_decisions = []
    for task_claim in task_decisions.order_by("-decided_at", "-pk")[:50]:
        task_claim.history_type = "task_decision"
        task_claim.history_timestamp = task_claim.decided_at
        rejected_task_decisions.append(task_claim)
    proposal_history = list(proposal_decisions.order_by("-decided_at", "-pk")[:50])
    for proposal in proposal_history:
        proposal.history_type = "proposal_decision"
        proposal.history_timestamp = proposal.decided_at
    goal_events = list(goal_events_query.order_by("-created_at", "-pk")[:50])
    for event in goal_events:
        event.history_type = "goal_event"
        event.history_timestamp = event.created_at
        event.child = event.goal.child
    history_entries = sorted(
        [
            *ledger_entries,
            *rejected_reward_decisions,
            *rejected_task_decisions,
            *proposal_history,
            *goal_events,
        ],
        key=lambda entry: (entry.history_timestamp, entry.pk),
        reverse=True,
    )[:50]
    ledger_page = Paginator(history_entries, 10).get_page(
        request.GET.get("history_page", 1)
    )
    task_source_ids = [
        entry.source_id
        for entry in ledger_page.object_list
        if (
            entry.history_type == "ledger"
            and entry.kind == LedgerKind.TASK
            and entry.source_id
        )
    ]
    history_claims = {
        claim.pk: claim
        for claim in TaskClaim.objects.filter(pk__in=task_source_ids).select_related(
            "decided_by"
        )
    }
    assigned_task_source_ids = [
        entry.source_id
        for entry in ledger_page.object_list
        if (
            entry.history_type == "ledger"
            and entry.kind == LedgerKind.ASSIGNED_TASK
            and entry.source_id
        )
    ]
    history_assigned_tasks = {
        item.pk: item
        for item in AssignedTask.objects.filter(pk__in=assigned_task_source_ids).select_related(
            "batch__assigned_by"
        )
    }
    for entry in ledger_page.object_list:
        if entry.history_type == "ledger":
            entry.task_claim = history_claims.get(entry.source_id)
            entry.assigned_task = history_assigned_tasks.get(entry.source_id)
            actor = entry.actor
            actor_label = ""
            if entry.kind == LedgerKind.TASK and entry.task_claim:
                actor = entry.task_claim.decided_by or actor
                actor_label = _("Approved by")
            elif entry.kind == LedgerKind.REWARD and entry.reward_request:
                actor = entry.reward_request.decided_by or actor
                actor_label = _("Approved by")
            elif entry.kind == LedgerKind.ASSIGNED_TASK and entry.assigned_task:
                actor = entry.assigned_task.batch.assigned_by
                actor_label = _("Assigned by")
            elif entry.kind == LedgerKind.PENALTY:
                actor_label = _("Added by")
            elif entry.kind == LedgerKind.ADJUSTMENT:
                actor_label = _("Adjusted by")
            elif entry.kind == LedgerKind.SAVINGS_RETURN:
                actor_label = _("Returned by")
            elif entry.kind in {LedgerKind.SAVINGS_TRANSFER, LedgerKind.GOAL_COMPLETION}:
                actor_label = _("Added by") if entry.kind == LedgerKind.SAVINGS_TRANSFER else _("Approved by")
            entry.history_actor = actor
            entry.history_actor_label = actor_label if actor else ""
    for proposal in proposal_history:
        proposal.history_actor_label = _("Approved by") if proposal.status == RequestStatus.APPROVED else _("Rejected by")
    for event in goal_events:
        event.history_actor_label = {
            GoalActivityType.CREATED: _("Added by"),
            GoalActivityType.CLOSED: _("Deleted by"),
            GoalActivityType.RETURNED: _("Returned by"),
            GoalActivityType.CURRENT_CHANGED: _("Adjusted by"),
            GoalActivityType.MODE_SELECTED: _("Adjusted by"),
            GoalActivityType.COMPLETED: _("Approved by"),
        }.get(event.event_type, _("Added by")) if event.actor else ""
    history_preserved_params = [
        (key, value)
        for key in request.GET
        if key
        not in {
            "history_child",
            "history_page",
            "history_date",
            "history_activity",
            "history_start",
            "history_end",
        }
        for value in request.GET.getlist(key)
    ]
    history_pagination_params = [
        *history_preserved_params,
        ("history_child", history_child_id),
        ("history_activity", history_activity),
        ("history_date", history_date if history_date != "any" else ""),
        ("history_start", history_custom_start if history_date == "custom" else ""),
        ("history_end", history_custom_end if history_date == "custom" else ""),
    ]
    history_pagination_params = [(key, value) for key, value in history_pagination_params if value]
    history_pagination_query = urlencode(history_pagination_params)
    if history_pagination_query:
        history_pagination_query += "&"
    history_child_name = next(
        (child.name for child in history_children if str(child.pk) == history_child_id),
        "",
    )
    history_activity_label = {
        "tasks": _("Tasks"),
        "penalties": _("Penalties"),
        "rewards": _("Rewards"),
        "goals": _("Goals"),
        "gifts": _("Gifts"),
        "scratch": _("Scratch tickets"),
        "adjustments": _("Point adjustments"),
    }.get(history_activity, "")
    pending_requests = _pending_request_items(goals_by_child)
    parent_accounts = list(get_user_model().objects.filter(is_active=True).order_by("username"))

    return render(
        request,
        "economy/parent_dashboard.html",
        {
            "children": children,
            "today": today,
            "pending_requests": pending_requests,
            "pending_count": len(pending_requests),
            "tasks": Task.objects.filter(is_deleted=False),
            "active_tasks": Task.objects.filter(is_active=True, is_deleted=False),
            "penalties": PenaltyTemplate.objects.filter(is_deleted=False),
            "active_penalties": PenaltyTemplate.objects.filter(
                is_active=True,
                is_deleted=False,
            ),
            "rewards": Reward.objects.filter(is_deleted=False),
            "goals": all_goals,
            "goal_children": children,
            "ledger_page": ledger_page,
            "history_children": history_children,
            "history_child_id": history_child_id,
            "history_child_name": history_child_name,
            "history_date": history_date,
            "history_custom_start": history_custom_start,
            "history_custom_end": history_custom_end,
            "history_date_error": history_date_error,
            "history_activity": history_activity,
            "history_activity_label": history_activity_label,
            "history_filter_count": sum(
                bool(value)
                for value in (
                    history_child_id,
                    history_activity,
                    history_date != "any" or history_custom_start or history_custom_end,
                )
            ),
            "history_filters_active": bool(
                history_child_id
                or history_activity
                or history_date != "any"
                or history_custom_start
                or history_custom_end
            ),
            "history_preserved_params": history_preserved_params,
            "history_pagination_query": history_pagination_query,
            "task_form": TaskForm(auto_id="id_new_task_%s"),
            "penalty_form": PenaltyForm(auto_id="id_new_penalty_%s"),
            "reward_form": RewardForm(auto_id="id_new_reward_%s"),
            "parent_account_form": ParentAccountForm(auto_id="id_new_parent_%s"),
            "child_account_form": ChildAccountForm(auto_id="id_new_child_%s"),
            "family_preferences_form": FamilyPreferencesForm(
                instance=FamilySettings.load(),
                auto_id="id_family_preferences_%s",
            ),
            "network_access_form": NetworkAccessForm(
                instance=FamilySettings.load(),
                current_ip=client_ip(request),
                auto_id="id_network_access_%s",
            ),
            "current_client_ip": client_ip(request),
            "paired_devices": DeviceToken.objects.filter(
                revoked_at__isnull=True
            ).select_related("created_by"),
            "current_device": current_device(request),
            "backup_status": backup_status(),
            "backup_settings_form": BackupSettingsForm(),
            "smtp_status": public_smtp_config(),
            "smtp_settings_form": SmtpSettingsForm(
                initial=public_smtp_config(),
                auto_id="id_smtp_settings_%s",
            ),
            "backup_audit_events": BackupAuditEvent.objects.select_related("actor")[:5],
            "feedback_page": feedback_page,
            "feedback_status": feedback_status,
            "feedback_type": feedback_type,
            "feedback_status_choices": FeedbackStatus.choices,
            "feedback_type_choices": FeedbackType.choices,
            "parent_account_items": [
                {
                    "account": account,
                    "form": ParentEditForm(
                        account=account,
                        auto_id=f"id_parent_{account.pk}_%s",
                    ),
                }
                for account in parent_accounts
            ],
            "child_account_items": [
                {
                    "child": child,
                    "form": ChildEditForm(
                        child=child,
                        auto_id=f"id_child_{child.pk}_%s",
                    ),
                }
                for child in children
            ],
        },
    )


@parent_required
@require_POST
def parent_create_catalog(request, kind):
    forms = {"task": TaskForm, "penalty": PenaltyForm, "reward": RewardForm}
    form_class = forms.get(kind)
    if form_class is None:
        raise Http404
    form = form_class(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, _("Catalog item created."))
    else:
        messages.error(request, _("Check the entered data."))
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")


@parent_required
@require_POST
def parent_create_parent_account(request):
    form = ParentAccountForm(request.POST)
    if form.is_valid():
        user = form.save()
        messages.success(request, _("Parent account “%(username)s” created.") % {"username": user.username})
    else:
        messages.error(request, _("Check the new parent account details."))
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_create_child_account(request):
    form = ChildAccountForm(request.POST)
    if form.is_valid():
        child = form.save()
        messages.success(request, _("Child profile “%(name)s” created.") % {"name": child.name})
    else:
        messages.error(request, _("Check the new child profile details."))
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_edit_parent_account(request, account_id):
    account = get_object_or_404(get_user_model(), pk=account_id, is_active=True)
    form = ParentEditForm(request.POST, account=account)
    if form.is_valid():
        form.save()
        if account.pk == request.user.pk and form.cleaned_data.get("new_password"):
            update_session_auth_hash(request, account)
        messages.success(request, _("Parent account “%(username)s” updated.") % {"username": account.username})
    else:
        messages.error(request, _("Check the parent account details."))
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_remove_parent_account(request, account_id):
    account = get_object_or_404(get_user_model(), pk=account_id, is_active=True)
    if account.pk == request.user.pk:
        messages.error(request, _("You cannot remove the account you are currently using."))
    elif get_user_model().objects.filter(is_active=True).count() <= 1:
        messages.error(request, _("You cannot remove the last active parent account."))
    else:
        account.is_active = False
        account.save(update_fields=["is_active"])
        messages.success(request, _("Parent account “%(username)s” removed.") % {"username": account.username})
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_edit_child_account(request, child_id):
    child = get_object_or_404(ChildProfile, pk=child_id, is_active=True)
    form = ChildEditForm(request.POST, child=child)
    if form.is_valid():
        form.save(actor=request.user)
        messages.success(request, _("Child profile “%(name)s” updated.") % {"name": child.name})
    else:
        messages.error(request, _("Check the child profile details."))
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_decide_birth_date(request, request_id, decision):
    try:
        with transaction.atomic():
            change = (
                BirthDateChangeRequest.objects.select_for_update()
                .select_related("child")
                .get(pk=request_id)
            )
            if change.status != RequestStatus.PENDING:
                raise ValidationError(_("This request has already been resolved."))
            if decision == "approve":
                change.child.birth_date = change.requested_birth_date
                change.child.birth_date_initialized = True
                change.child.save(
                    update_fields=["birth_date", "birth_date_initialized"]
                )
                change.status = RequestStatus.APPROVED
                success_message = _("Birthday change approved.")
            elif decision == "reject":
                change.status = RequestStatus.REJECTED
                success_message = _("Birthday change rejected.")
            else:
                raise Http404
            change.decided_by = request.user
            change.decided_at = timezone.now()
            change.save(update_fields=["status", "decided_by", "decided_at"])
        notify_birth_date_decision(change, approved=decision == "approve")
        messages.success(request, success_message)
    except BirthDateChangeRequest.DoesNotExist:
        raise Http404
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_remove_child_account(request, child_id):
    child = get_object_or_404(ChildProfile, pk=child_id, is_active=True)
    child.is_active = False
    child.save(update_fields=["is_active"])
    messages.success(request, _("Child profile “%(name)s” removed.") % {"name": child.name})
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_edit_catalog(request, kind, item_id):
    forms = {"task": TaskForm, "penalty": PenaltyForm, "reward": RewardForm}
    models = {"task": Task, "penalty": PenaltyTemplate, "reward": Reward}
    form_class = forms.get(kind)
    model = models.get(kind)
    if form_class is None or model is None:
        raise Http404
    item = get_object_or_404(model, pk=item_id, is_deleted=False)
    form = form_class(request.POST, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, _("“%(title)s” updated.") % {"title": item.title})
    else:
        messages.error(request, _("Check the edited data."))
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")


@parent_required
@require_POST
def parent_toggle_catalog(request, kind, item_id):
    models = {"task": Task, "penalty": PenaltyTemplate, "reward": Reward}
    model = models.get(kind)
    if model is None:
        raise Http404
    item = get_object_or_404(model, pk=item_id, is_deleted=False)
    item.is_active = not item.is_active
    item.save(update_fields=["is_active"])
    messages.success(
        request,
        _("“%(title)s” is now %(state)s.")
        % {"title": item.title, "state": _("visible") if item.is_active else _("hidden")},
    )
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")


@parent_required
@require_POST
def parent_delete_catalog(request, kind, item_id):
    models = {"task": Task, "penalty": PenaltyTemplate, "reward": Reward}
    model = models.get(kind)
    if model is None:
        raise Http404
    item = get_object_or_404(model, pk=item_id, is_deleted=False)
    item.is_active = False
    item.is_deleted = True
    item.save(update_fields=["is_active", "is_deleted"])
    messages.success(request, _("“%(title)s” deleted.") % {"title": item.title})
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")


@parent_required
@require_POST
def parent_decide_task(request, claim_id, decision):
    claim = get_object_or_404(TaskClaim, pk=claim_id)
    try:
        if decision == "approve":
            approve_task_claim(claim=claim, actor=request.user)
            claim.refresh_from_db()
            notify_task_decision(claim, approved=True)
            messages.success(request, _("Task approved."))
        elif decision == "reject":
            form = TaskDecisionCommentForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_("Check the comment."))
            claim = reject_task_claim(
                claim=claim,
                actor=request.user,
                reason=form.cleaned_data["reason"],
            )
            notify_task_decision(claim, approved=False)
            messages.success(request, _("Task rejected."))
        elif decision == "revise":
            form = TaskDecisionCommentForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_("Check the comment."))
            request_task_revision(
                claim=claim,
                actor=request.user,
                reason=form.cleaned_data["reason"],
            )
            claim.refresh_from_db()
            notify_task_revision(claim)
            messages.success(request, _("The task was returned for improvements."))
        else:
            raise Http404
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_decide_reward(request, request_id, decision):
    reward_request = get_object_or_404(RewardRequest, pk=request_id)
    try:
        if decision == "approve":
            approve_reward_request(request=reward_request, actor=request.user)
            reward_request.refresh_from_db()
            notify_reward_decision(reward_request, approved=True)
            messages.success(request, _("Reward approved."))
        elif decision == "reject":
            form = RejectForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_("A rejection reason is required."))
            with transaction.atomic():
                locked = RewardRequest.objects.select_for_update().get(pk=reward_request.pk)
                if locked.status != RequestStatus.PENDING:
                    raise ValidationError(_("This request has already been resolved."))
                locked.status = RequestStatus.REJECTED
                locked.rejection_reason = form.cleaned_data["reason"]
                locked.decided_by = request.user
                locked.decided_at = timezone.now()
                locked.save(
                    update_fields=[
                        "status",
                        "rejection_reason",
                        "decided_by",
                        "decided_at",
                    ]
                )
            notify_reward_decision(locked, approved=False)
            messages.success(request, _("Reward request rejected."))
        else:
            raise Http404
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_decide_proposal(request, proposal_id, decision):
    proposal = get_object_or_404(Proposal, pk=proposal_id)
    try:
        if decision == "approve":
            form = ApprovalCostForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_("Enter the final point amount."))
            approve_proposal(
                proposal=proposal,
                actor=request.user,
                final_cost=form.cleaned_data["final_cost"],
                goal_mode=request.POST.get("goal_mode") or None,
            )
            proposal.refresh_from_db()
            notify_proposal_decision(proposal, approved=True)
            messages.success(request, _("Suggestion approved."))
        elif decision == "reject":
            form = RejectForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_("A rejection reason is required."))
            proposal.status = RequestStatus.REJECTED
            proposal.parent_note = form.cleaned_data["reason"]
            proposal.decided_by = request.user
            proposal.decided_at = timezone.now()
            proposal.save(
                update_fields=["status", "parent_note", "decided_by", "decided_at"]
            )
            notify_proposal_decision(proposal, approved=False)
            messages.success(request, _("Suggestion rejected."))
        else:
            raise Http404
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_decide_goal_completion(request, request_id, decision):
    completion_request = get_object_or_404(
        GoalCompletionRequest,
        pk=request_id,
        goal__child__is_active=True,
    )
    try:
        if decision == "complete":
            approve_goal_completion(
                completion_request=completion_request,
                actor=request.user,
            )
            messages.success(request, _("Goal completed."))
        elif decision == "keep_active":
            keep_goal_active(
                completion_request=completion_request,
                actor=request.user,
            )
            messages.info(request, _("The goal will stay active."))
        else:
            raise Http404
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('parent_dashboard')}#parent-home")


@parent_required
@require_POST
def parent_add_goal_points(request, goal_id):
    goal = get_object_or_404(
        SavingsGoal,
        pk=goal_id,
        child__is_active=True,
        status=GoalStatus.ACTIVE,
    )
    form = GoalAmountForm(request.POST)
    try:
        if not form.is_valid():
            raise ValidationError(_("Enter a valid point amount."))
        add_saved_points(
            goal=goal,
            child=goal.child,
            amount=form.cleaned_data["amount"],
            actor=request.user,
        )
        messages.success(request, _("Points were saved for this goal."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")


@parent_required
@require_POST
def parent_return_goal_points(request, goal_id):
    goal = get_object_or_404(
        SavingsGoal,
        pk=goal_id,
        child__is_active=True,
        status=GoalStatus.ACTIVE,
    )
    try:
        amount = return_saved_points(goal=goal, actor=request.user)
        messages.success(
            request,
            _("%(amount)s points are available for rewards again.") % {"amount": amount},
        )
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")


@parent_required
@require_POST
def parent_edit_goal(request, goal_id):
    goal = get_object_or_404(
        SavingsGoal,
        pk=goal_id,
        child__is_active=True,
        status=GoalStatus.ACTIVE,
    )
    form = SavingsGoalForm(request.POST, instance=goal)
    try:
        if not form.is_valid():
            raise ValidationError(_("Check the goal details."))
        update_savings_goal(
            goal=goal,
            title=form.cleaned_data["title"],
            target_amount=form.cleaned_data["target_amount"],
            icon=form.cleaned_data["icon"],
            actor=request.user,
        )
        messages.success(request, _("Goal updated."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")


@parent_required
@require_POST
def parent_close_goal(request, goal_id):
    goal = get_object_or_404(
        SavingsGoal,
        pk=goal_id,
        child__is_active=True,
        status=GoalStatus.ACTIVE,
    )
    try:
        close_savings_goal(goal=goal, actor=request.user)
        messages.success(request, _("Goal closed."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")


@parent_required
@require_POST
def parent_delete_goal(request, goal_id):
    goal = get_object_or_404(
        SavingsGoal,
        pk=goal_id,
        child__is_active=True,
        status=GoalStatus.ACTIVE,
    )
    try:
        _deleted_goal, returned_amount = delete_savings_goal(
            goal=goal,
            actor=request.user,
        )
        if returned_amount:
            messages.success(
                request,
                _("Goal deleted and %(amount)s points returned.")
                % {"amount": returned_amount},
            )
        else:
            messages.success(request, _("Goal deleted."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('parent_dashboard')}#parent-catalogs")


@parent_required
@require_POST
def parent_adjust_balance(request, child_id):
    child = get_object_or_404(ChildProfile, pk=child_id)
    form = AdjustmentForm(request.POST)
    if form.is_valid():
        post_ledger_entry(
            child=child,
            delta=form.cleaned_data["amount"],
            kind=LedgerKind.ADJUSTMENT,
            description=form.cleaned_data["description"],
            actor=request.user,
        )
        messages.success(request, _("Balance adjusted."))
    else:
        messages.error(request, _("Check the balance adjustment."))
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_apply_penalty(request, child_id):
    child = get_object_or_404(ChildProfile, pk=child_id)
    form = ApplyPenaltyForm(request.POST)
    if form.is_valid():
        penalty = get_object_or_404(
            PenaltyTemplate,
            pk=form.cleaned_data["penalty_id"],
            is_active=True,
        )
        post_ledger_entry(
            child=child,
            delta=penalty.amount,
            kind=LedgerKind.PENALTY,
            description=f"{penalty.title}: {form.cleaned_data['reason']}",
            actor=request.user,
            source_id=penalty.pk,
        )
        messages.success(request, _("Penalty assigned."))
    else:
        messages.error(request, _("A reason is required."))
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_award_task(request, child_id):
    child = get_object_or_404(ChildProfile, pk=child_id, is_active=True)
    form = AwardTasksForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Choose at least one active task."))
        return redirect("parent_dashboard")

    tasks = list(form.cleaned_data["task_ids"])
    with transaction.atomic():
        for task in tasks:
            post_ledger_entry(
                child=child,
                delta=task.reward,
                kind=LedgerKind.TASK,
                description=task.title,
                actor=request.user,
                source_id=task.pk,
            )
            TaskCompletion.objects.create(child=child, task=task)
    total = sum(task.reward for task in tasks)
    messages.success(
        request,
        _("%(name)s received %(count)s task(s) (total +%(total)s).")
        % {"name": child.name, "count": len(tasks), "total": total},
    )
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_assign_tasks(request, child_id):
    child = get_object_or_404(ChildProfile, pk=child_id, is_active=True)
    form = AssignTasksForm(request.POST)
    if not form.is_valid():
        error = next(iter(form.errors.values()))[0]
        messages.error(request, str(error))
        return redirect("parent_dashboard")
    try:
        batch = assign_tasks(
            child=child,
            actor=request.user,
            tasks=list(form.cleaned_data["task_ids"]),
            custom_title=form.cleaned_data["custom_title"],
            custom_points=form.cleaned_data["custom_points"],
            blocks_rewards=form.cleaned_data["blocks_rewards"],
        )
        notify_assigned_tasks(batch)
        messages.success(
            request,
            _("Tasks were assigned to %(name)s for today.")
            % {"name": child.name},
        )
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_cancel_assigned_task(request, assigned_task_id):
    assigned_task = get_object_or_404(
        AssignedTask.objects.select_related("batch"),
        pk=assigned_task_id,
        batch__child__is_active=True,
    )
    try:
        cancel_assigned_task(assigned_task=assigned_task, actor=request.user)
        messages.success(request, _("The assigned task was cancelled."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_cancel_assigned_task_batch(request, batch_id):
    batch = get_object_or_404(
        AssignedTaskBatch,
        pk=batch_id,
        child__is_active=True,
    )
    cancelled = cancel_assigned_task_batch(batch=batch, actor=request.user)
    if cancelled:
        messages.success(request, _("The remaining assigned tasks were cancelled."))
    else:
        messages.info(request, _("There are no waiting tasks to cancel."))
    return redirect("parent_dashboard")


@child_required
@require_POST
def child_complete_assigned_task(request, assigned_task_id):
    assigned_task = get_object_or_404(
        AssignedTask,
        pk=assigned_task_id,
        batch__child=request.child,
    )
    completed = False
    try:
        complete_assigned_task(
            assigned_task=assigned_task,
            child=request.child,
        )
        messages.success(
            request,
            _("Assigned task completed. You received your points."),
            extra_tags="task-success",
        )
        completed = True
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return _child_action_response(
        request,
        ok=completed,
        effect="task" if completed else None,
    )


@parent_required
@require_POST
def parent_assign_child_penalty(request, child_id):
    child = get_object_or_404(ChildProfile, pk=child_id, is_active=True)
    form = AssignPenaltiesForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Choose at least one active penalty."))
        return redirect("parent_dashboard")

    penalties = list(form.cleaned_data["penalty_ids"])
    reason = form.cleaned_data["reason"].strip()
    with transaction.atomic():
        for penalty in penalties:
            description = penalty.title if not reason else f"{penalty.title}: {reason}"
            post_ledger_entry(
                child=child,
                delta=penalty.amount,
                kind=LedgerKind.PENALTY,
                description=description,
                actor=request.user,
                source_id=penalty.pk,
            )
    total = sum(penalty.amount for penalty in penalties)
    messages.success(
        request,
        _("%(name)s received %(count)s penalty/penalties (total %(total)s).")
        % {"name": child.name, "count": len(penalties), "total": total},
    )
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_assign_penalty(request, penalty_id):
    penalty = get_object_or_404(PenaltyTemplate, pk=penalty_id, is_active=True)
    child = get_object_or_404(
        ChildProfile,
        pk=request.POST.get("child_id"),
        is_active=True,
    )
    reason = request.POST.get("reason", "").strip()
    if not reason:
        messages.error(request, _("A reason is required."))
        return redirect("parent_dashboard")
    post_ledger_entry(
        child=child,
        delta=penalty.amount,
        kind=LedgerKind.PENALTY,
        description=f"{penalty.title}: {reason}",
        actor=request.user,
        source_id=penalty.pk,
    )
    messages.success(
        request,
        _("Penalty “%(penalty)s” assigned to %(name)s.")
        % {"penalty": penalty.title, "name": child.name},
    )
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_set_min_balance(request, child_id):
    child = get_object_or_404(ChildProfile, pk=child_id)
    form = MinBalanceForm(request.POST)
    if form.is_valid():
        child.min_balance = form.cleaned_data["min_balance"]
        child.save(update_fields=["min_balance"])
        messages.success(request, _("Credit limit changed."))
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_unlock_child(request, child_id):
    child = get_object_or_404(ChildProfile, pk=child_id)
    child.failed_pin_attempts = 0
    child.locked_until = None
    child.save(update_fields=["failed_pin_attempts", "locked_until"])
    messages.success(request, _("%(name)s unlocked.") % {"name": child.name})
    return redirect("parent_dashboard")


@parent_required
@require_POST
def parent_update_family_preferences(request):
    family = FamilySettings.load()
    form = FamilyPreferencesForm(request.POST, instance=family)
    if form.is_valid():
        form.save()
        messages.success(request, _("Family settings saved."))
    else:
        messages.error(request, _("Check the family settings."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")


@parent_required
@require_POST
def parent_update_network_access(request):
    if not request.user.is_staff:
        messages.error(
            request,
            _("Only a parent administrator can change network access."),
        )
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    family = FamilySettings.load()
    form = NetworkAccessForm(
        request.POST,
        instance=family,
        current_ip=client_ip(request),
    )
    if not form.is_valid():
        messages.error(request, _("Check the network access settings."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    authenticated = authenticate(
        request,
        username=request.user.get_username(),
        password=form.cleaned_data["current_password"],
    )
    if authenticated is None:
        messages.error(request, _("The current parent password is incorrect."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    family = form.save()
    SecurityAuditEvent.objects.create(
        actor=request.user,
        action=SecurityAuditEvent.Action.NETWORK_POLICY_CHANGED,
        detail=family.network_access_mode,
    )
    messages.success(request, _("Network access settings saved."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")


@parent_required
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


@parent_required
@require_POST
def parent_configure_smtp(request):
    if not request.user.is_staff:
        messages.error(request, _("Only a parent administrator can change email settings."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    form = SmtpSettingsForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Check the email settings."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    authenticated = authenticate(
        request,
        username=request.user.get_username(),
        password=form.cleaned_data["current_password"],
    )
    if authenticated is None:
        messages.error(request, _("The current parent password is incorrect."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    config = {
        key: form.cleaned_data[key]
        for key in (
            "enabled",
            "host",
            "port",
            "security",
            "username",
            "password",
            "from_email",
            "feedback_email",
        )
    }
    try:
        verify_smtp(config)
        save_smtp_config(config)
    except (OSError, ValueError, smtplib.SMTPException):
        logger.warning("SMTP settings verification failed", exc_info=True)
        messages.error(
            request,
            _("Email settings were not saved. Check the server details and credentials."),
        )
    else:
        messages.success(request, _("Email settings were verified and saved."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")


@parent_required
@require_POST
def parent_configure_backup(request):
    if not request.user.is_staff:
        messages.error(request, _("Only a parent administrator can change backup settings."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    form = BackupSettingsForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Check the backup settings."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    authenticated = authenticate(
        request,
        username=request.user.get_username(),
        password=form.cleaned_data["current_password"],
    )
    if authenticated is None:
        messages.error(request, _("The current parent password is incorrect."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    try:
        status = configure_backup(form.cleaned_data)
    except RuntimeError as exc:
        messages.error(request, _("Backup settings were not saved: %(error)s") % {"error": exc})
    else:
        BackupAuditEvent.objects.create(
            actor=request.user,
            action=BackupAuditEvent.Action.CONFIGURED,
            provider=status.get("provider", ""),
            target=status.get("target", ""),
        )
        messages.success(request, _("Backup storage was verified and saved."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")


@parent_required
@require_POST
def parent_run_backup(request):
    if not request.user.is_staff:
        messages.error(request, _("Only a parent administrator can start a backup."))
        return redirect(f"{reverse('parent_dashboard')}#parent-settings")
    try:
        request_manual_backup()
    except RuntimeError as exc:
        messages.error(request, _("The backup could not be started: %(error)s") % {"error": exc})
    else:
        status = backup_status()
        BackupAuditEvent.objects.create(
            actor=request.user,
            action=BackupAuditEvent.Action.MANUAL_RUN,
            provider=status.get("provider", ""),
            target=status.get("target", ""),
        )
        messages.success(request, _("Backup started. Refresh this page to see its status."))
    return redirect(f"{reverse('parent_dashboard')}#parent-settings")


@parent_required
@require_POST
def push_subscribe(request):
    import json

    try:
        payload = json.loads(request.body)
        keys = payload["keys"]
        PushSubscription.objects.update_or_create(
            endpoint=payload["endpoint"],
            defaults={
                "user": request.user,
                "child": None,
                "device": None,
                "p256dh": keys["p256dh"],
                "auth": keys["auth"],
                "user_agent": request.headers.get("User-Agent", "")[:255],
            },
        )
    except (KeyError, TypeError, ValueError):
        return JsonResponse({"ok": False}, status=400)
    return JsonResponse({"ok": True})


@parent_required
@require_POST
def push_unsubscribe(request):
    import json

    try:
        endpoint = json.loads(request.body)["endpoint"]
    except (KeyError, TypeError, ValueError):
        return JsonResponse({"ok": False}, status=400)
    PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
    return JsonResponse({"ok": True})


@child_required
@require_POST
def child_push_subscribe(request):
    import json

    try:
        payload = json.loads(request.body)
        keys = payload["keys"]
        device = current_device(request)
        if device is None and settings.DEVICE_PAIRING_REQUIRED:
            return JsonResponse({"ok": False}, status=403)
        if device is None:
            device, _unused_token = DeviceToken.issue(
                created_by=None,
                label=_("Development device"),
            )
        PushSubscription.objects.update_or_create(
            endpoint=payload["endpoint"],
            defaults={
                "user": None,
                "child": request.child,
                "device": device,
                "p256dh": keys["p256dh"],
                "auth": keys["auth"],
                "user_agent": request.headers.get("User-Agent", "")[:255],
            },
        )
    except (KeyError, TypeError, ValueError):
        return JsonResponse({"ok": False}, status=400)
    return JsonResponse({"ok": True})


@child_required
@require_POST
def child_push_unsubscribe(request):
    import json

    try:
        endpoint = json.loads(request.body)["endpoint"]
    except (KeyError, TypeError, ValueError):
        return JsonResponse({"ok": False}, status=400)
    PushSubscription.objects.filter(
        child=request.child,
        device=current_device(request),
        endpoint=endpoint,
    ).delete()
    return JsonResponse({"ok": True})


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


def offline(request):
    return render(request, "economy/offline.html")
