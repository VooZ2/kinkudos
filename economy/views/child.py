import hashlib
import json
import os
import time
from uuid import uuid4

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db.models import Count, Max, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from economy.auth import (
    child_object_or_404,
    child_required,
    ensure_media_accessible,
)
from economy.forms import (
    AvatarForm,
    BirthDateForm,
    ChangePinForm,
    FirstThemeForm,
    GoalAmountForm,
    PointGiftForm,
    ProposalForm,
    TaskEvidenceForm,
    ThemeForm,
)
from economy.images import (
    ImageProcessingError,
    process_avatar,
    process_task_evidence,
)
from economy.lottery import (
    lottery_state,
    purchase_lottery_ticket,
    reveal_lottery_ticket,
)
from economy.models import (
    AssignedTask,
    AssignedTaskBatch,
    AssignedTaskStatus,
    BirthDateChangeRequest,
    ChildProfile,
    FamilySettings,
    GoalCompletionRequest,
    GoalStatus,
    LedgerKind,
    LotteryTicket,
    RequestStatus,
    Reward,
    RewardRequest,
    SavingsGoal,
    SavingsGoalEvent,
    Task,
    TaskClaim,
    TaskCompletion,
)
from economy.push import (
    notify_birth_date_change,
    notify_gift_received,
    notify_proposal,
    notify_reward_request,
    notify_task_claim,
)
from economy.services import (
    add_saved_points,
    assigned_tasks_block_rewards,
    cancel_reward_request,
    complete_assigned_task,
    request_goal_completion,
    resubmit_task_claim,
    reward_is_affordable,
    reward_requests_blocked,
    select_goal_mode,
    submit_reward_request,
    submit_task,
    transfer_points,
)


def _debug_log(*, hypothesis_id, location, message, data):
    # region agent log
    open(
        os.path.expanduser("/opt/cursor/logs/debug.log"),
        "a",
    ).write(
        json.dumps(
            {
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data,
                "timestamp": int(time.time() * 1000),
            }
        )
        + "\n"
    )
    # endregion


@child_required
def child_dashboard(request):
    child = request.child
    try:
        greeting_name = (child.address_name or "").strip()
    except (AttributeError, TypeError):
        greeting_name = ""
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
    waiting_for_parents = _waiting_for_parents_items(child)
    return render(
        request,
        "economy/child_dashboard.html",
        {
            "child": child,
            "greeting_name": greeting_name,
            "tasks": Task.objects.filter(is_active=True, is_deleted=False),
            "rewards": rewards,
            "pending_task_ids": pending_task_ids,
            "pending_reward_ids": pending_reward_ids,
            "waiting_for_parents": waiting_for_parents,
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


def _waiting_for_parents_items(child, *, limit=3):
    """Compact chips for items still waiting on a parent decision."""
    items = []
    for claim in child.task_claims.filter(
        status=RequestStatus.NEEDS_CHANGES
    ).select_related("task").order_by("submitted_at", "pk"):
        items.append(
            {
                "kind": "revision",
                "kind_label": _("Needs a fix"),
                "title": claim.task_title,
                "href": f"#revision-claim-{claim.pk}",
            }
        )
    for claim in child.task_claims.filter(
        status=RequestStatus.PENDING
    ).select_related("task").order_by("submitted_at", "pk"):
        task = claim.task
        if task is None or not task.is_active or task.is_deleted:
            continue
        items.append(
            {
                "kind": "task",
                "kind_label": _("Task"),
                "title": claim.task_title,
                "href": f"#task-card-{task.pk}",
            }
        )
    for reward_request in child.reward_requests.filter(
        status=RequestStatus.PENDING
    ).select_related("reward").order_by("submitted_at", "pk"):
        reward = reward_request.reward
        if reward is None or not reward.is_active or reward.is_deleted:
            continue
        items.append(
            {
                "kind": "reward",
                "kind_label": _("Reward"),
                "title": reward_request.reward_title,
                "href": f"#reward-card-{reward.pk}",
            }
        )
    for completion in GoalCompletionRequest.objects.filter(
        goal__child=child,
        status=RequestStatus.PENDING,
        goal__status=GoalStatus.ACTIVE,
    ).select_related("goal").order_by("requested_at", "pk"):
        items.append(
            {
                "kind": "goal",
                "kind_label": _("Goal"),
                "title": completion.goal.title,
                "href": f"#goal-card-{completion.goal_id}",
            }
        )
    for proposal in child.proposals.filter(
        status=RequestStatus.PENDING
    ).order_by("created_at", "pk"):
        items.append(
            {
                "kind": "proposal",
                "kind_label": _("Idea"),
                "title": proposal.title,
                "href": "#pasiulymai",
            }
        )
    if child.birth_date_change_requests.filter(status=RequestStatus.PENDING).exists():
        items.append(
            {
                "kind": "birthday",
                "kind_label": _("Birthday"),
                "title": _("Birthday change"),
                "href": "#gimtadienis",
            }
        )
    return items[:limit]

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
            child_note=form.cleaned_data.get("child_note") or "",
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
    claim = child_object_or_404(
        request,
        TaskClaim.objects.all(),
        pk=claim_id,
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
        resubmit_task_claim(
            claim=claim,
            child_note=form.cleaned_data.get("child_note") or "",
        )
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
    claim = child_object_or_404(
        request,
        TaskClaim.objects.all(),
        pk=claim_id,
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
        messages.success(request, _("Your surprise card is ready."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect(f"{reverse('child_dashboard')}#prizai")

@child_required
@require_POST
def child_reveal_lottery_ticket(request, ticket_id):
    ticket = child_object_or_404(request, LotteryTicket.objects.all(), pk=ticket_id)
    revealed = reveal_lottery_ticket(ticket=ticket, child=request.child)
    revealed.refresh_from_db()
    return JsonResponse(
        {
            "ok": True,
            "delta": revealed.applied_delta,
            "balance": revealed.result_ledger_entry.balance_after,
            "matching_value": revealed.prize_amount,
            "values": revealed.values,
        }
    )

@child_required
@require_POST
def child_cancel_reward(request, request_id):
    reward_request = child_object_or_404(
        request,
        RewardRequest.objects.all(),
        pk=request_id,
    )
    cancelled = cancel_reward_request(request=reward_request, child=request.child)
    if not cancelled:
        return redirect("child_dashboard")
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
    goal = child_object_or_404(
        request,
        SavingsGoal.objects.all(),
        pk=goal_id,
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
    goal = child_object_or_404(
        request,
        SavingsGoal.objects.all(),
        pk=goal_id,
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
    goal = child_object_or_404(
        request,
        SavingsGoal.objects.all(),
        pk=goal_id,
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
    return redirect(f"{reverse('child_dashboard')}#nustatymai")

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
    return redirect(f"{reverse('child_dashboard')}#gimtadienis")

def _status_counts(queryset, field="status"):
    return list(
        queryset.values(field)
        .annotate(c=Count("pk"))
        .order_by(field)
        .values_list(field, "c")
    )


def _relation_watermark(queryset, *timestamp_fields):
    aggregates = {
        "count": Count("pk"),
        "max_pk": Max("pk"),
    }
    for field in timestamp_fields:
        aggregates[f"max_{field}"] = Max(field)
    return queryset.aggregate(**aggregates)


def _child_state_payload(child):
    family_settings = FamilySettings.load()
    raw_state = json.dumps(
        {
            "local_date": timezone.localdate(),
            "child": [
                child.pk,
                child.name,
                child.theme,
                child.theme_selected,
                child.randomize_theme_daily,
                child.theme_randomized_on,
                child.birth_date,
                child.birth_date_initialized,
                child.avatar.name if child.avatar else "",
                child.balance,
                child.min_balance,
                child.lottery_enabled,
            ],
            "family": [
                family_settings.photo_bonus_points,
                family_settings.lottery_enabled,
                family_settings.lottery_ticket_cost,
                family_settings.lottery_weekly_limit,
            ],
            "ledger": _relation_watermark(
                child.ledger_entries.all(),
                "created_at",
            ),
            "tasks": {
                **_relation_watermark(
                    child.task_claims.all(),
                    "submitted_at",
                    "decided_at",
                    "child_acknowledged_at",
                    "evidence_uploaded_at",
                    "evidence_purged_at",
                ),
                "statuses": _status_counts(child.task_claims.all()),
            },
            "rewards": {
                **_relation_watermark(
                    child.reward_requests.all(),
                    "submitted_at",
                    "decided_at",
                ),
                "statuses": _status_counts(child.reward_requests.all()),
            },
            "assigned_tasks": {
                **_relation_watermark(
                    AssignedTask.objects.filter(batch__child=child),
                    "completed_at",
                    "cancelled_at",
                ),
                "statuses": _status_counts(
                    AssignedTask.objects.filter(batch__child=child)
                ),
                "batches": list(
                    AssignedTaskBatch.objects.filter(child=child)
                    .order_by("pk")
                    .values_list(
                        "pk",
                        "blocks_rewards",
                        "assigned_on",
                        "created_at",
                    )
                ),
            },
            "lottery": {
                **_relation_watermark(
                    child.lottery_tickets.all(),
                    "purchased_at",
                    "revealed_at",
                ),
                "statuses": _status_counts(child.lottery_tickets.all()),
            },
            "goals": list(
                child.goals.annotate(
                    _saved_amount=Coalesce(
                        Sum(
                            "contributions__amount",
                            filter=Q(contributions__state="active"),
                        ),
                        Value(0),
                    )
                )
                .order_by("pk")
                .values_list(
                    "pk",
                    "title",
                    "icon",
                    "mode",
                    "status",
                    "target_amount",
                    "_saved_amount",
                )
            ),
            "goal_completions": {
                **_relation_watermark(
                    GoalCompletionRequest.objects.filter(goal__child=child),
                    "requested_at",
                    "decided_at",
                ),
                "statuses": _status_counts(
                    GoalCompletionRequest.objects.filter(goal__child=child)
                ),
            },
            "goal_events": _relation_watermark(
                SavingsGoalEvent.objects.filter(goal__child=child),
                "created_at",
            ),
            "proposals": {
                **_relation_watermark(
                    child.proposals.all(),
                    "created_at",
                    "decided_at",
                ),
                "statuses": _status_counts(child.proposals.all()),
            },
            "birth_dates": {
                **_relation_watermark(
                    child.birth_date_change_requests.all(),
                    "requested_at",
                    "decided_at",
                ),
                "statuses": _status_counts(child.birth_date_change_requests.all()),
            },
            "task_catalog": list(
                Task.objects.filter(is_active=True, is_deleted=False)
                .order_by("sort_order", "title", "pk")
                .values_list("pk", "title", "icon", "reward")
            ),
            "reward_catalog": list(
                Reward.objects.filter(is_active=True, is_deleted=False)
                .order_by("sort_order", "title", "pk")
                .values_list("pk", "title", "icon", "cost")
            ),
            "task_completions": _relation_watermark(
                TaskCompletion.objects.filter(child=child),
                "completed_on",
                "created_at",
            ),
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
        return redirect(f"{reverse('child_dashboard')}#pinas")
    child = request.child
    if child.is_locked:
        messages.error(
            request,
            _("The profile is temporarily locked. Try again later."),
        )
        return redirect(f"{reverse('child_dashboard')}#pinas")
    if not child.verify_pin(form.cleaned_data["current_pin"]):
        messages.error(request, _("The current PIN is incorrect."))
        return redirect(f"{reverse('child_dashboard')}#pinas")
    child.set_pin(form.cleaned_data["new_pin"])
    child.save(update_fields=["pin_hash"])
    messages.success(request, _("PIN changed."))
    return redirect(f"{reverse('child_dashboard')}#pinas")

@child_required
@require_POST
def child_set_avatar(request):
    form = AvatarForm(request.POST, request.FILES)
    if not form.is_valid():
        error = next(iter(form.errors.values()))[0]
        messages.error(request, str(error))
        return redirect(f"{reverse('child_dashboard')}#nustatymai")

    upload = form.cleaned_data["avatar"]
    try:
        avatar_bytes = process_avatar(upload)
    except ImageProcessingError:
        messages.error(request, _("The image could not be processed. Choose another file."))
        return redirect(f"{reverse('child_dashboard')}#nustatymai")

    child = request.child
    old_name = child.avatar.name
    file_name = f"{slugify(child.name) or 'vaikas'}-{uuid4().hex}.webp"
    child.avatar.save(file_name, ContentFile(avatar_bytes), save=False)
    child.save(update_fields=["avatar"])
    if old_name:
        child.avatar.storage.delete(old_name)
    messages.success(request, _("Avatar changed."))
    return redirect(f"{reverse('child_dashboard')}#nustatymai")

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
    child = get_object_or_404(ChildProfile, pk=child_id, is_active=True)
    ensure_media_accessible(request, child)
    if not child.avatar:
        raise Http404
    response = FileResponse(child.avatar.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "private, max-age=300"
    response["X-Content-Type-Options"] = "nosniff"
    return response

def task_evidence(request, claim_id, size):
    claim = get_object_or_404(TaskClaim.objects.select_related("child"), pk=claim_id)
    ensure_media_accessible(request, claim.child, require_child_session=True)
    field = claim.evidence_thumbnail if size == "thumbnail" else claim.evidence_image
    if size not in {"thumbnail", "full"} or not field:
        raise Http404
    response = FileResponse(field.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "private, max-age=300"
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = "inline"
    return response

@child_required
@require_POST
def child_complete_assigned_task(request, assigned_task_id):
    started_at = time.perf_counter()
    _debug_log(
        hypothesis_id="H3",
        location="economy/views/child.py:child_complete_assigned_task",
        message="entry",
        data={"assignedTaskId": assigned_task_id, "childId": request.child.pk},
    )
    assigned_task = get_object_or_404(
        AssignedTask,
        pk=assigned_task_id,
        batch__child=request.child,
    )
    completed = False
    try:
        service_started = time.perf_counter()
        complete_assigned_task(
            assigned_task=assigned_task,
            child=request.child,
        )
        _debug_log(
            hypothesis_id="H3",
            location="economy/views/child.py:child_complete_assigned_task",
            message="service complete",
            data={
                "service_ms": round((time.perf_counter() - service_started) * 1000, 2),
            },
        )
        messages.success(
            request,
            _("Assigned task completed. You received your points."),
            extra_tags="task-success",
        )
        completed = True
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    _debug_log(
        hypothesis_id="H5",
        location="economy/views/child.py:child_complete_assigned_task",
        message="exit",
        data={
            "completed": completed,
            "total_ms": round((time.perf_counter() - started_at) * 1000, 2),
        },
    )
    return _child_action_response(
        request,
        ok=completed,
        effect="task" if completed else None,
    )
