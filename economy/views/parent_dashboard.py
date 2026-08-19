import hashlib
import json
import os
import time
from datetime import date, datetime, time, timedelta
from urllib.parse import urlencode

from django.contrib.auth import (
    get_user_model,
)
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET

from economy.auth import (
    accessible_children_qs,
    current_caregiver,
    current_device,
    parent_required,
)
from economy.email_config import public_smtp_config
from economy.forms import (
    BackupSettingsForm,
    ChildAccountForm,
    ChildEditForm,
    FamilyPreferencesForm,
    NetworkAccessForm,
    ParentAccountForm,
    ParentEditForm,
    PenaltyForm,
    RewardForm,
    SmtpSettingsForm,
    TaskForm,
)
from economy.lottery import (
    lottery_state,
)
from economy.models import (
    AssignedTask,
    AssignedTaskStatus,
    BackupAuditEvent,
    BirthDateChangeRequest,
    ChildProfile,
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
    PenaltyTemplate,
    Proposal,
    ProposalType,
    RequestStatus,
    Reward,
    RewardRequest,
    SavingsGoal,
    SavingsGoalEvent,
    Task,
    TaskClaim,
)
from economy.net import client_ip
from economy.services import (
    unavailable_assignment_task_ids,
)
from economy.views.caregiver import caregiver_settings_context


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


def _pending_request_items(goals_by_child, *, child_ids=None):
    pending_requests = []
    child_filter = {"child_id__in": child_ids} if child_ids is not None else {}
    pending_claims = list(
        TaskClaim.objects.filter(
            status=RequestStatus.PENDING,
            child__is_active=True,
            **child_filter,
        )
        .select_related("child", "task")
        .order_by("submitted_at", "pk")
    )
    pending_rewards = list(
        RewardRequest.objects.filter(
            status=RequestStatus.PENDING,
            child__is_active=True,
            **child_filter,
        )
        .select_related("child", "reward")
        .order_by("submitted_at", "pk")
    )
    pending_proposals = list(
        Proposal.objects.filter(
            status=RequestStatus.PENDING,
            child__is_active=True,
            **child_filter,
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
            **({"goal__child_id__in": child_ids} if child_ids is not None else {}),
        )
        .select_related("goal", "goal__child")
        .order_by("requested_at", "pk")
    )
    goals_by_id = {
        goal.pk: goal
        for goals in goals_by_child.values()
        for goal in goals
    }
    for completion in pending_goal_completions:
        if completion.goal_id in goals_by_id:
            completion.goal = goals_by_id[completion.goal_id]
    pending_birth_date_changes = list(
        BirthDateChangeRequest.objects.filter(
            status=RequestStatus.PENDING,
            child__is_active=True,
            **({"child_id__in": child_ids} if child_ids is not None else {}),
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

def _pending_request_revision(pending_requests):
    """Return a stable fingerprint for the rendered pending-request state."""

    state = []
    for item in pending_requests:
        child = item["child"]
        common = [
            item["kind"],
            child.pk,
            child.name,
            child.avatar.name if child.avatar else "",
            item["submitted_at"],
        ]
        if item["kind"] == "task":
            claim = item["claim"]
            state.append(
                [
                    *common,
                    claim.pk,
                    claim.status,
                    claim.task_title,
                    claim.reward_snapshot,
                    claim.photo_bonus_snapshot,
                    claim.evidence_image.name if claim.evidence_image else "",
                    claim.evidence_thumbnail.name if claim.evidence_thumbnail else "",
                ]
            )
        elif item["kind"] == "reward":
            reward_request = item["reward_request"]
            state.append(
                [
                    *common,
                    reward_request.pk,
                    reward_request.status,
                    reward_request.reward_title,
                    reward_request.cost_snapshot,
                ]
            )
        elif item["kind"] == "proposal":
            proposal = item["proposal"]
            state.append(
                [
                    *common,
                    proposal.pk,
                    proposal.status,
                    proposal.proposal_type,
                    proposal.title,
                    proposal.suggested_cost,
                    proposal.goal_mode,
                    proposal.replaces_current_goal,
                ]
            )
        elif item["kind"] == "goal":
            completion = item["completion"]
            goal = completion.goal
            state.append(
                [
                    *common,
                    completion.pk,
                    completion.status,
                    goal.pk,
                    goal.title,
                    goal.mode,
                    goal.progress_amount,
                    goal.target_amount,
                ]
            )
        else:
            change = item["change"]
            state.append(
                [
                    *common,
                    change.pk,
                    change.status,
                    change.previous_birth_date,
                    change.requested_birth_date,
                ]
            )
    canonical = json.dumps(
        {"count": len(pending_requests), "items": state},
        default=str,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def _parent_pending_state_data(request=None):
    children = list(accessible_children_qs(request) if request is not None else ChildProfile.objects.filter(is_active=True))
    child_ids = [child.pk for child in children]
    goals = list(
        SavingsGoal.objects.filter(child__is_active=True, child_id__in=child_ids)
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
    goals_by_child = {child.pk: [] for child in children}
    for goal in goals:
        goals_by_child.setdefault(goal.child_id, []).append(goal)
    pending_requests = _pending_request_items(goals_by_child, child_ids=child_ids)
    return pending_requests, _pending_request_revision(pending_requests)

def _pending_requests_fragment(request, pending_requests, pending_revision):
    return render_to_string(
        "economy/includes/pending_requests.html",
        {
            "pending_requests": pending_requests,
            "pending_count": len(pending_requests),
            "pending_revision": pending_revision,
        },
        request=request,
    )

@parent_required
@require_GET
def parent_pending_state(request):
    pending_requests, pending_revision = _parent_pending_state_data(request)
    etag = f'"{pending_revision}"'
    response_headers = {
        "Cache-Control": "private, no-store",
        "Vary": "Cookie",
        "ETag": etag,
    }
    supplied_etags = {
        value.strip()
        for value in request.headers.get("If-None-Match", "").split(",")
    }
    if etag in supplied_etags or pending_revision in supplied_etags:
        response = HttpResponse(status=304)
    else:
        response = JsonResponse(
            {
                "count": len(pending_requests),
                "revision": pending_revision,
                "html": _pending_requests_fragment(
                    request,
                    pending_requests,
                    pending_revision,
                ),
            }
        )
    for header, value in response_headers.items():
        response[header] = value
    return response

@parent_required
def parent_dashboard(request):
    started_at = time.perf_counter()
    caregiver = current_caregiver(request)
    is_caregiver = caregiver is not None
    children = list(accessible_children_qs(request))
    child_ids = [child.pk for child in children]
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
        SavingsGoal.objects.filter(child__is_active=True, child_id__in=child_ids or [-1])
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
            goal__child_id__in=child_ids or [-1],
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
        child.saved_assignment_presets = list(child.assignment_presets.all())
        child.assignment_batches = list(
            child.assigned_task_batches.filter(assigned_on=today)
            .select_related("assigned_by")
            .prefetch_related("items__task", "items__cancelled_by")
        )
        for batch in child.assignment_batches:
            batch.has_pending_items = any(
                item.status == AssignedTaskStatus.PENDING
                for item in batch.items.all()
            )
    history_children = list(accessible_children_qs(request).order_by("name"))
    if child_ids:
        ledger_child_filter = {"child_id__in": child_ids}
        goal_child_filter = {"goal__child_id__in": child_ids}
    else:
        ledger_child_filter = {"child_id__in": [-1]}
        goal_child_filter = {"goal__child_id__in": [-1]}
    feedback_status = request.GET.get("feedback_status", "active").strip()
    feedback_type = request.GET.get("feedback_type", "").strip()
    feedback_query = FeedbackReport.objects.select_related("parent", "child")
    if is_caregiver:
        feedback_query = feedback_query.filter(child_id__in=child_ids or [-1])
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
    ledger_query = LedgerEntry.objects.filter(**ledger_child_filter).select_related(
        "child", "actor"
    )
    if history_cutoff is not None:
        ledger_query = ledger_query.filter(created_at__gte=history_cutoff)
    if history_end_at is not None:
        ledger_query = ledger_query.filter(created_at__lte=history_end_at)
    reward_decisions = RewardRequest.objects.filter(
        status__in=[RequestStatus.APPROVED, RequestStatus.REJECTED],
        decided_at__isnull=False,
        **ledger_child_filter,
    ).select_related("child", "decided_by")
    if history_cutoff is not None:
        reward_decisions = reward_decisions.filter(decided_at__gte=history_cutoff)
    if history_end_at is not None:
        reward_decisions = reward_decisions.filter(decided_at__lte=history_end_at)
    task_decisions = TaskClaim.objects.filter(
        status=RequestStatus.REJECTED,
        decided_at__isnull=False,
        **ledger_child_filter,
    ).select_related("child", "decided_by", "task")
    if history_cutoff is not None:
        task_decisions = task_decisions.filter(decided_at__gte=history_cutoff)
    if history_end_at is not None:
        task_decisions = task_decisions.filter(decided_at__lte=history_end_at)
    proposal_decisions = Proposal.objects.filter(
        status__in=[RequestStatus.APPROVED, RequestStatus.REJECTED],
        decided_at__isnull=False,
        **ledger_child_filter,
    ).select_related("child", "decided_by")
    if history_cutoff is not None:
        proposal_decisions = proposal_decisions.filter(decided_at__gte=history_cutoff)
    if history_end_at is not None:
        proposal_decisions = proposal_decisions.filter(decided_at__lte=history_end_at)
    goal_events_query = SavingsGoalEvent.objects.filter(
        goal__child__is_active=True,
        **goal_child_filter,
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
    ledger_entries = list(ledger_query.order_by("-created_at", "-pk"))
    reward_decisions = list(reward_decisions.order_by("-decided_at", "-pk"))
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
    for task_claim in task_decisions.order_by("-decided_at", "-pk"):
        task_claim.history_type = "task_decision"
        task_claim.history_timestamp = task_claim.decided_at
        rejected_task_decisions.append(task_claim)
    proposal_history = list(proposal_decisions.order_by("-decided_at", "-pk"))
    for proposal in proposal_history:
        proposal.history_type = "proposal_decision"
        proposal.history_timestamp = proposal.decided_at
    goal_events = list(goal_events_query.order_by("-created_at", "-pk"))
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
    )
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
        "scratch": _("Surprise cards"),
        "adjustments": _("Point adjustments"),
    }.get(history_activity, "")
    pending_requests = _pending_request_items(goals_by_child, child_ids=child_ids)
    pending_revision = _pending_request_revision(pending_requests)
    parent_accounts = list(
        get_user_model()
        .objects.filter(is_active=True, caregiver_profile__isnull=True)
        .order_by("username")
    )

    context = {
            "children": children,
            "is_caregiver": is_caregiver,
            "caregiver_profile": caregiver,
            "today": today,
            "pending_requests": pending_requests,
            "pending_count": len(pending_requests),
            "pending_revision": pending_revision,
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
            # Keep inactive-but-unrevoked devices visible so every parent can
            # review and revoke a token that still grants child access.
            "paired_devices": list(
                DeviceToken.objects.filter(revoked_at__isnull=True)
                .select_related("created_by")
            ),
            "has_paired_devices": DeviceToken.objects.filter(
                revoked_at__isnull=True
            ).exists(),
            "device_pairing_share": request.session.pop("device_pairing_share", None),
            "current_device": current_device(request),
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
                        actor=request.user,
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
        }
    if not is_caregiver:
        context.update(caregiver_settings_context(request))
    _debug_log(
        hypothesis_id="H5",
        location="economy/views/parent_dashboard.py:parent_dashboard",
        message="render context built",
        data={
            "children_count": len(children),
            "pending_count": len(pending_requests),
            "history_count": len(history_entries),
            "total_ms": round((time.perf_counter() - started_at) * 1000, 2),
        },
    )
    return render(
        request,
        "economy/parent_dashboard.html",
        context,
    )
