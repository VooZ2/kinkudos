import random
import json
import os
import time
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Exists, Sum
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import (
    AssignedTask,
    AssignedTaskBatch,
    AssignedTaskStatus,
    AssignmentPreset,
    AssignmentPresetCadence,
    AssignmentPresetItem,
    AssignmentPresetWeekendMode,
    BirthdayAward,
    ChildProfile,
    FamilySettings,
    GoalActivityType,
    GoalCompletionRequest,
    GoalMode,
    GoalStatus,
    LedgerEntry,
    LedgerKind,
    PointGift,
    Proposal,
    ProposalType,
    PushSubscription,
    RequestStatus,
    Reward,
    RewardRequest,
    SavingsContribution,
    SavingsContributionState,
    SavingsGoal,
    SavingsGoalEvent,
    TaskClaim,
    TaskCompletion,
    Theme,
)

ASSIGNMENT_PRESET_LIMIT = 5


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


def deactivate_parent_account(account):
    """Deactivate an active parent while preserving account invariants."""

    user_model = get_user_model()
    other_active_parents = user_model.objects.filter(
        is_active=True,
    ).exclude(pk=account.pk)
    deactivation = user_model.objects.filter(
        pk=account.pk,
        is_active=True,
    ).filter(Exists(other_active_parents))
    if account.is_staff:
        other_active_administrators = user_model.objects.filter(
            is_active=True,
            is_staff=True,
        ).exclude(pk=account.pk)
        deactivation = deactivation.filter(Exists(other_active_administrators))

    with transaction.atomic():
        deactivated = deactivation.update(is_active=False)
        if deactivated:
            PushSubscription.objects.filter(user=account).delete()
    return deactivated


@transaction.atomic
def post_ledger_entry(*, child, delta, kind, description, actor=None, source_id=None, enforce_limit=False):
    locked_child = ChildProfile.objects.select_for_update().get(pk=child.pk)
    new_balance = locked_child.balance + delta
    if enforce_limit and new_balance < locked_child.min_balance:
        raise ValidationError(
            _("This operation would exceed the allowed %(limit)s point limit.")
            % {"limit": locked_child.min_balance}
        )
    entry = LedgerEntry.objects.create(
        child=locked_child,
        delta=delta,
        balance_after=new_balance,
        kind=kind,
        description=description,
        actor=actor,
        source_id=source_id,
    )
    locked_child.balance = new_balance
    locked_child.save(update_fields=["balance"])
    return entry


@transaction.atomic
def transfer_points(*, sender, recipient, amount):
    if sender.pk == recipient.pk:
        raise ValidationError(_("You cannot give points to yourself."))
    if amount <= 0:
        raise ValidationError(_("The gift amount must be greater than zero."))

    locked = {
        child.pk: child
        for child in ChildProfile.objects.select_for_update()
        .filter(pk__in=[sender.pk, recipient.pk], is_active=True)
        .order_by("pk")
    }
    if sender.pk not in locked or recipient.pk not in locked:
        raise ValidationError(_("The selected child profile is not available."))
    locked_sender = locked[sender.pk]
    locked_recipient = locked[recipient.pk]
    if locked_sender.balance <= 0 or amount > locked_sender.balance:
        raise ValidationError(_("You can give only points you have already earned."))

    gift = PointGift.objects.create(
        sender=locked_sender,
        recipient=locked_recipient,
        amount=amount,
    )
    sender_balance = locked_sender.balance - amount
    recipient_balance = locked_recipient.balance + amount
    LedgerEntry.objects.create(
        child=locked_sender,
        delta=-amount,
        balance_after=sender_balance,
        kind=LedgerKind.GIFT,
        description=_("Gift to %(name)s") % {"name": locked_recipient.name},
        source_id=gift.pk,
    )
    LedgerEntry.objects.create(
        child=locked_recipient,
        delta=amount,
        balance_after=recipient_balance,
        kind=LedgerKind.GIFT,
        description=_("Gift from %(name)s") % {"name": locked_sender.name},
        source_id=gift.pk,
    )
    locked_sender.balance = sender_balance
    locked_recipient.balance = recipient_balance
    locked_sender.save(update_fields=["balance"])
    locked_recipient.save(update_fields=["balance"])
    return gift


def _birthday_occurs_on(birth_date, current_date):
    month, day = birth_date.month, birth_date.day
    if month == 2 and day == 29:
        try:
            birth_date.replace(year=current_date.year)
        except ValueError:
            day = 28
    return (month, day) == (current_date.month, current_date.day)


def award_birthdays(*, current_date=None):
    current_date = current_date or timezone.localdate()
    points = FamilySettings.load().birthday_points
    if points <= 0:
        return []

    awarded = []
    children = ChildProfile.objects.filter(
        is_active=True, birth_date__isnull=False
    )
    for child in children:
        if not _birthday_occurs_on(child.birth_date, current_date):
            continue
        try:
            with transaction.atomic():
                locked_child = ChildProfile.objects.select_for_update().get(pk=child.pk)
                award, created = BirthdayAward.objects.get_or_create(
                    child=locked_child,
                    year=current_date.year,
                    defaults={"points": points},
                )
                if not created:
                    continue
                entry = post_ledger_entry(
                    child=locked_child,
                    delta=points,
                    kind=LedgerKind.BIRTHDAY,
                    description=_("Birthday gift"),
                    source_id=award.pk,
                )
                award.ledger_entry = entry
                award.save(update_fields=["ledger_entry"])
                awarded.append(award)
        except IntegrityError:
            continue
    return awarded


def randomize_daily_themes(*, current_date=None, chooser=None):
    current_date = current_date or timezone.localdate()
    chooser = chooser or random.SystemRandom().choice
    changed = []
    child_ids = ChildProfile.objects.filter(
        is_active=True,
        randomize_theme_daily=True,
    ).values_list("pk", flat=True)

    for child_id in child_ids:
        with transaction.atomic():
            child = ChildProfile.objects.select_for_update().get(pk=child_id)
            if child.theme_randomized_on == current_date:
                continue
            available_themes = [
                value for value, _label in Theme.choices if value != child.theme
            ]
            if not available_themes:
                continue
            child.theme = chooser(available_themes)
            child.theme_selected = True
            child.theme_randomized_on = current_date
            child.save(
                update_fields=[
                    "theme",
                    "theme_selected",
                    "theme_randomized_on",
                ]
            )
            changed.append(child)
    return changed


def submit_task(*, child, task, photo_bonus_snapshot=0, child_note=""):
    if not task.is_active:
        raise ValidationError(_("This task is no longer active."))
    try:
        with transaction.atomic():
            return TaskClaim.objects.create(
                child=child,
                task=task,
                task_title=task.title,
                reward_snapshot=task.reward,
                photo_bonus_snapshot=photo_bonus_snapshot,
                child_note=child_note.strip()[:200],
            )
    except IntegrityError as exc:
        raise ValidationError(_("This task is already awaiting approval.")) from exc


@transaction.atomic
def approve_task_claim(*, claim, actor):
    started_at = time.perf_counter()
    locked = TaskClaim.objects.select_related("child").get(pk=claim.pk)
    if locked.status != RequestStatus.PENDING:
        raise ValidationError(_("This request has already been resolved."))
    decided_at = timezone.now()
    claimed = TaskClaim.objects.filter(
        pk=locked.pk,
        status=RequestStatus.PENDING,
    ).update(
        status=RequestStatus.APPROVED,
        decided_by=actor,
        decided_at=decided_at,
    )
    if not claimed:
        raise ValidationError(_("This request has already been resolved."))
    entry = post_ledger_entry(
        child=locked.child,
        delta=locked.total_reward,
        kind=LedgerKind.TASK,
        description=locked.task_title,
        actor=actor,
        source_id=locked.pk,
    )
    before_completion = time.perf_counter()
    ensure_task_completion(child=locked.child, task=locked.task)
    _debug_log(
        hypothesis_id="H1",
        location="economy/services.py:approve_task_claim",
        message="service segments",
        data={
            "claimId": locked.pk,
            "post_ledger_and_update_ms": round(
                (before_completion - started_at) * 1000, 2
            ),
            "ensure_task_completion_ms": round(
                (time.perf_counter() - before_completion) * 1000, 2
            ),
            "total_ms": round((time.perf_counter() - started_at) * 1000, 2),
        },
    )
    return entry


def reject_task_claim(*, claim, actor, reason):
    with transaction.atomic():
        decided_at = timezone.now()
        claimed = TaskClaim.objects.filter(
            pk=claim.pk,
            status=RequestStatus.PENDING,
        ).update(
            status=RequestStatus.REJECTED,
            rejection_reason=reason.strip(),
            decided_by=actor,
            decided_at=decided_at,
        )
        if not claimed:
            raise ValidationError(_("This request has already been resolved."))
        return TaskClaim.objects.get(pk=claim.pk)


def request_task_revision(*, claim, actor, reason):
    with transaction.atomic():
        decided_at = timezone.now()
        claimed = TaskClaim.objects.filter(
            pk=claim.pk,
            status=RequestStatus.PENDING,
        ).update(
            status=RequestStatus.NEEDS_CHANGES,
            revision_note=reason.strip(),
            decided_by=actor,
            decided_at=decided_at,
        )
        if not claimed:
            raise ValidationError(_("This request has already been resolved."))
        return TaskClaim.objects.get(pk=claim.pk)


def resubmit_task_claim(*, claim, child_note=None):
    with transaction.atomic():
        submitted_at = timezone.now()
        updates = {
            "status": RequestStatus.PENDING,
            "revision_note": "",
            "decided_by": None,
            "decided_at": None,
            "submitted_at": submitted_at,
        }
        if child_note is not None:
            updates["child_note"] = child_note.strip()[:200]
        claimed = TaskClaim.objects.filter(
            pk=claim.pk,
            status=RequestStatus.NEEDS_CHANGES,
        ).update(**updates)
        if not claimed:
            raise ValidationError(_("This task is not awaiting corrections."))
        return TaskClaim.objects.get(pk=claim.pk)


def reward_requests_blocked(child):
    credit_limit = abs(min(child.min_balance, 0))
    if credit_limit == 0:
        return False
    used_credit = max(0, -child.balance)
    return used_credit * 2 >= credit_limit


def assigned_tasks_block_rewards(child):
    return AssignedTask.objects.filter(
        batch__child=child,
        batch__blocks_rewards=True,
        batch__assigned_on=timezone.localdate(),
        status=AssignedTaskStatus.PENDING,
    ).exists()


def assigned_task_nudge_at(*, now=None):
    """Schedule the soft nudge ~3h later, but still on the assignment day.

    Assigned work expires at local midnight. A nudge_at that falls after that
    would never send (send_due requires assigned_on == today), so late-evening
    batches clamp to the same local evening instead.
    """
    now = now or timezone.now()
    local_now = timezone.localtime(now)
    day_end = local_now.replace(hour=23, minute=45, second=0, microsecond=0)
    candidate = now + timedelta(hours=3)
    if timezone.localtime(candidate) > day_end:
        candidate = day_end
    if candidate < now:
        candidate = now
    return candidate


def ensure_task_completion(*, child, task, completed_on=None):
    """Mark a catalog task as credited today for Assign/Award day gating.

    Children may submit and have the same catalog task approved multiple times
    in one day. The unique (child, task, completed_on) row is only a day marker
    for parent Assign/Award — never a reason to fail a second credit.
    """
    if task is None:
        return None
    completed_on = completed_on or timezone.localdate()
    completion, _created = TaskCompletion.objects.get_or_create(
        child=child,
        task=task,
        completed_on=completed_on,
    )
    return completion


def unavailable_assignment_task_ids(child):
    today = timezone.localdate()
    pending_claim_ids = child.task_claims.filter(
        status__in=[RequestStatus.PENDING, RequestStatus.NEEDS_CHANGES]
    ).values_list("task_id", flat=True)
    active_assignment_ids = AssignedTask.objects.filter(
        batch__child=child,
        batch__assigned_on=today,
        status=AssignedTaskStatus.PENDING,
        task__isnull=False,
    ).values_list("task_id", flat=True)
    completed_ids = child.task_completions.filter(
        completed_on=today
    ).values_list("task_id", flat=True)
    return set(pending_claim_ids) | set(active_assignment_ids) | set(completed_ids)


def custom_assignment_title_taken_today(child, title):
    """True when a same-title custom assigned task is still counting for today."""
    title = (title or "").strip()
    if not title:
        return False
    today = timezone.localdate()
    return AssignedTask.objects.filter(
        batch__child=child,
        batch__assigned_on=today,
        task__isnull=True,
        title_snapshot=title,
        status__in=[AssignedTaskStatus.PENDING, AssignedTaskStatus.COMPLETED],
    ).exists()


@transaction.atomic
def assign_tasks(
    *,
    child,
    actor,
    tasks,
    custom_title="",
    custom_points=None,
    blocks_rewards=False,
    task_notes=None,
    custom_note="",
):
    child = ChildProfile.objects.select_for_update().get(
        pk=child.pk,
        is_active=True,
    )
    task_ids = [task.pk for task in tasks]
    unavailable = unavailable_assignment_task_ids(child)
    if unavailable.intersection(task_ids):
        raise ValidationError(
            _("One or more selected tasks are no longer available today.")
        )
    notes = task_notes or {}
    custom_note = (custom_note or "").strip()
    now = timezone.now()
    batch = AssignedTaskBatch.objects.create(
        child=child,
        assigned_by=actor,
        blocks_rewards=blocks_rewards,
        nudge_at=assigned_task_nudge_at(now=now),
    )
    AssignedTask.objects.bulk_create(
        [
            AssignedTask(
                batch=batch,
                task=task,
                title_snapshot=task.title,
                icon_snapshot=task.icon,
                reward_snapshot=task.reward,
                note_snapshot=(notes.get(task.pk) or "").strip(),
            )
            for task in tasks
        ]
    )
    if custom_title:
        AssignedTask.objects.create(
            batch=batch,
            title_snapshot=custom_title,
            icon_snapshot="🧹",
            reward_snapshot=custom_points,
            note_snapshot=custom_note,
        )
    return batch


def assignment_preset_matches_date(preset, day):
    weekday = day.weekday()
    if preset.cadence == AssignmentPresetCadence.DAILY:
        return True
    if preset.cadence == AssignmentPresetCadence.WEEKDAYS:
        return bool(preset.weekday_mask & (1 << weekday))
    if preset.cadence == AssignmentPresetCadence.WEEKEND:
        if preset.weekend_mode == AssignmentPresetWeekendMode.SATURDAY:
            return weekday == 5
        if preset.weekend_mode == AssignmentPresetWeekendMode.SUNDAY:
            return weekday == 6
        return weekday in {5, 6}
    if preset.cadence == AssignmentPresetCadence.WEEKLY:
        return preset.weekly_weekday == weekday
    return False


@transaction.atomic
def save_assignment_preset(
    *,
    child,
    actor,
    name,
    tasks,
    task_notes=None,
    custom_title="",
    custom_points=None,
    custom_note="",
    blocks_rewards=False,
    cadence=AssignmentPresetCadence.DAILY,
    weekday_mask=0,
    weekend_mode=AssignmentPresetWeekendMode.BOTH,
    weekly_weekday=None,
    run_at=None,
):
    from datetime import time as dt_time

    child = ChildProfile.objects.select_for_update().get(pk=child.pk, is_active=True)
    name = (name or "").strip()
    if not name:
        raise ValidationError(_("Enter a name for this saved set."))
    if AssignmentPreset.objects.filter(child=child).count() >= ASSIGNMENT_PRESET_LIMIT:
        raise ValidationError(_("You can save up to %(limit)s sets per child.") % {
            "limit": ASSIGNMENT_PRESET_LIMIT,
        })
    custom_title = (custom_title or "").strip()
    if bool(custom_title) != bool(custom_points):
        raise ValidationError(
            _("Enter both the custom task name and its point amount.")
        )
    if not tasks and not custom_title:
        raise ValidationError(_("Choose at least one task or add a custom task."))
    if cadence == AssignmentPresetCadence.WEEKDAYS and not weekday_mask:
        raise ValidationError(_("Choose at least one weekday."))
    if cadence == AssignmentPresetCadence.WEEKLY and weekly_weekday is None:
        raise ValidationError(_("Choose a weekday for the weekly set."))
    if run_at is None:
        run_at = dt_time(7, 0)
    notes = task_notes or {}
    preset = AssignmentPreset.objects.create(
        child=child,
        name=name[:80],
        blocks_rewards=blocks_rewards,
        cadence=cadence,
        weekday_mask=weekday_mask if cadence == AssignmentPresetCadence.WEEKDAYS else 0,
        weekend_mode=(
            weekend_mode
            if cadence == AssignmentPresetCadence.WEEKEND
            else AssignmentPresetWeekendMode.BOTH
        ),
        weekly_weekday=(
            weekly_weekday if cadence == AssignmentPresetCadence.WEEKLY else None
        ),
        run_at=run_at,
        created_by=actor,
    )
    items = []
    for index, task in enumerate(tasks):
        items.append(
            AssignmentPresetItem(
                preset=preset,
                task=task,
                note=(notes.get(task.pk) or "").strip()[:200],
                sort_order=index,
            )
        )
    if custom_title:
        items.append(
            AssignmentPresetItem(
                preset=preset,
                custom_title=custom_title[:120],
                custom_points=custom_points,
                note=(custom_note or "").strip()[:200],
                sort_order=len(items),
            )
        )
    AssignmentPresetItem.objects.bulk_create(items)
    return preset


@transaction.atomic
def apply_assignment_preset(*, preset, actor=None):
    preset = (
        AssignmentPreset.objects.select_for_update()
        .select_related("child", "created_by")
        .prefetch_related("items__task")
        .get(pk=preset.pk)
    )
    child = ChildProfile.objects.select_for_update().get(
        pk=preset.child_id,
        is_active=True,
    )
    unavailable = unavailable_assignment_task_ids(child)
    catalog_tasks = []
    task_notes = {}
    custom_title = ""
    custom_points = None
    custom_note = ""
    for item in preset.items.all():
        if item.task_id:
            if item.task_id in unavailable:
                continue
            if not item.task.is_active or item.task.is_deleted:
                continue
            catalog_tasks.append(item.task)
            if item.note:
                task_notes[item.task_id] = item.note
        elif item.custom_title and not custom_title:
            custom_title = item.custom_title
            custom_points = item.custom_points
            custom_note = item.note
    if custom_title and custom_assignment_title_taken_today(child, custom_title):
        custom_title = ""
        custom_points = None
        custom_note = ""
    if not catalog_tasks and not custom_title:
        return None
    batch = assign_tasks(
        child=child,
        actor=actor or preset.created_by,
        tasks=catalog_tasks,
        custom_title=custom_title,
        custom_points=custom_points,
        blocks_rewards=preset.blocks_rewards,
        task_notes=task_notes,
        custom_note=custom_note,
    )
    AssignmentPreset.objects.filter(pk=preset.pk).update(
        last_auto_assigned_on=timezone.localdate(),
        updated_at=timezone.now(),
    )
    return batch


def run_due_assignment_presets(*, current_time=None):
    from .push import notify_assigned_tasks

    current_time = current_time or timezone.now()
    today = timezone.localdate()
    local_time = timezone.localtime(current_time).time()
    preset_ids = list(
        AssignmentPreset.objects.filter(is_paused=False, child__is_active=True)
        .exclude(last_auto_assigned_on=today)
        .values_list("pk", flat=True)
    )
    created = []
    for preset_id in preset_ids:
        batch = None
        with transaction.atomic():
            preset = (
                AssignmentPreset.objects.select_for_update()
                .select_related("child", "created_by")
                .get(pk=preset_id)
            )
            if preset.is_paused or not preset.child.is_active:
                continue
            if preset.last_auto_assigned_on == today:
                continue
            if not assignment_preset_matches_date(preset, today):
                continue
            if local_time < preset.run_at:
                continue
            batch = apply_assignment_preset(preset=preset, actor=preset.created_by)
            # Successful Apply stamps last_auto_assigned_on. An empty run must
            # not burn the day — retry on later ticks if work becomes available.
        if batch is not None:
            notify_assigned_tasks(batch)
            created.append(batch)
    return created


def send_due_assigned_task_nudges(*, current_time=None):
    from .push import notify_assigned_tasks_nudge

    current_time = current_time or timezone.now()
    today = timezone.localdate()
    due_ids = list(
        AssignedTaskBatch.objects.filter(
            nudge_at__isnull=False,
            nudge_at__lte=current_time,
            nudge_sent_at__isnull=True,
            assigned_on=today,
        ).values_list("pk", flat=True)
    )
    sent = []
    for batch_id in due_ids:
        should_notify = False
        with transaction.atomic():
            locked = (
                AssignedTaskBatch.objects.select_for_update()
                .select_related("child")
                .get(pk=batch_id)
            )
            if locked.nudge_sent_at is not None:
                continue
            if locked.assigned_on != timezone.localdate():
                locked.nudge_sent_at = current_time
                locked.save(update_fields=["nudge_sent_at"])
                continue
            has_pending = locked.items.filter(
                status=AssignedTaskStatus.PENDING
            ).exists()
            locked.nudge_sent_at = current_time
            locked.save(update_fields=["nudge_sent_at"])
            if has_pending and PushSubscription.objects.filter(
                child=locked.child
            ).exists():
                should_notify = True
                sent.append(locked)
        if should_notify:
            notify_assigned_tasks_nudge(locked)
    return sent


@transaction.atomic
def complete_assigned_task(*, assigned_task, child):
    started_at = time.perf_counter()
    today = timezone.localdate()
    completed_at = timezone.now()
    claimed = AssignedTask.objects.filter(
        pk=assigned_task.pk,
        batch__child=child,
        batch__assigned_on=today,
        status=AssignedTaskStatus.PENDING,
    ).update(
        status=AssignedTaskStatus.COMPLETED,
        completed_at=completed_at,
    )
    if not claimed:
        locked = AssignedTask.objects.select_related("batch", "task").get(
            pk=assigned_task.pk,
            batch__child=child,
        )
        if locked.status != AssignedTaskStatus.PENDING:
            raise ValidationError(_("This assigned task is no longer waiting."))
        raise ValidationError(_("This assigned task has expired."))
    locked = (
        AssignedTask.objects.select_related("batch", "task")
        .get(pk=assigned_task.pk, batch__child=child)
    )
    entry = post_ledger_entry(
        child=child,
        delta=locked.reward_snapshot,
        kind=LedgerKind.ASSIGNED_TASK,
        description=locked.title_snapshot,
        source_id=locked.pk,
    )
    before_completion = time.perf_counter()
    AssignedTask.objects.filter(pk=locked.pk).update(ledger_entry=entry)
    if locked.task_id:
        ensure_task_completion(child=child, task=locked.task)
    from .push import notify_assigned_task_completed

    before_notify = time.perf_counter()
    notify_assigned_task_completed(locked)
    _debug_log(
        hypothesis_id="H4",
        location="economy/services.py:complete_assigned_task",
        message="service segments",
        data={
            "assignedTaskId": locked.pk,
            "claim_and_ledger_ms": round((before_completion - started_at) * 1000, 2),
            "completion_and_link_ms": round(
                (before_notify - before_completion) * 1000, 2
            ),
            "notify_ms": round((time.perf_counter() - before_notify) * 1000, 2),
            "total_ms": round((time.perf_counter() - started_at) * 1000, 2),
        },
    )
    return entry


@transaction.atomic
def cancel_assigned_task(*, assigned_task, actor):
    today = timezone.localdate()
    cancelled_at = timezone.now()
    claimed = AssignedTask.objects.filter(
        pk=assigned_task.pk,
        batch__assigned_on=today,
        status=AssignedTaskStatus.PENDING,
    ).update(
        status=AssignedTaskStatus.CANCELLED,
        cancelled_at=cancelled_at,
        cancelled_by=actor,
    )
    if not claimed:
        locked = AssignedTask.objects.select_related("batch").get(pk=assigned_task.pk)
        if locked.status != AssignedTaskStatus.PENDING:
            raise ValidationError(_("Only a waiting assigned task can be cancelled."))
        raise ValidationError(_("This assigned task has expired."))
    return AssignedTask.objects.select_related("batch").get(pk=assigned_task.pk)


@transaction.atomic
def cancel_assigned_task_batch(*, batch, actor):
    if batch.assigned_on != timezone.localdate():
        return 0
    now = timezone.now()
    return AssignedTask.objects.select_for_update().filter(
        batch=batch,
        status=AssignedTaskStatus.PENDING,
    ).update(
        status=AssignedTaskStatus.CANCELLED,
        cancelled_at=now,
        cancelled_by=actor,
    )


def reward_is_affordable(child, reward):
    return child.balance - reward.cost >= child.min_balance


def _active_saved_amount(goal):
    return int(
        goal.contributions.filter(state=SavingsContributionState.ACTIVE).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )


def _record_goal_event(*, goal, event_type, description, actor=None, amount=None):
    return SavingsGoalEvent.objects.create(
        goal=goal,
        event_type=event_type,
        description=description,
        actor=actor,
        amount=amount,
    )


@transaction.atomic
def create_savings_goal(*, child, title, target_amount, icon="⭐", actor=None, mode=None):
    if target_amount <= 0:
        raise ValidationError(_("The goal target must be greater than zero."))
    locked_child = ChildProfile.objects.select_for_update().get(
        pk=child.pk,
        is_active=True,
    )
    goal = SavingsGoal.objects.create(
        child=locked_child,
        title=title.strip(),
        icon=icon,
        target_amount=target_amount,
        status=GoalStatus.ACTIVE,
    )
    _record_goal_event(
        goal=goal,
        event_type=GoalActivityType.CREATED,
        description=_("Goal created: %(title)s") % {"title": goal.title},
        actor=actor,
    )
    if mode is not None:
        goal = select_goal_mode(
            goal=goal,
            child=locked_child,
            mode=mode,
            actor=actor,
        )
    return goal


@transaction.atomic
def select_goal_mode(*, goal, child, mode, actor=None):
    if mode not in GoalMode.values:
        raise ValidationError(_("Choose a valid savings mode."))
    locked_child = ChildProfile.objects.select_for_update().get(
        pk=child.pk,
        is_active=True,
    )
    locked_goal = SavingsGoal.objects.select_for_update().get(
        pk=goal.pk,
        child=locked_child,
        status=GoalStatus.ACTIVE,
    )
    if locked_goal.mode == GoalMode.SAVED and mode != GoalMode.SAVED:
        if _active_saved_amount(locked_goal):
            raise ValidationError(
                _("Return the saved points before changing this goal's mode.")
            )
    previous_current = None
    if mode == GoalMode.AVAILABLE:
        previous_current = (
            SavingsGoal.objects.select_for_update()
            .filter(
                child=locked_child,
                status=GoalStatus.ACTIVE,
                mode=GoalMode.AVAILABLE,
            )
            .exclude(pk=locked_goal.pk)
            .first()
        )
        if previous_current:
            previous_current.mode = None
            previous_current.save(update_fields=["mode"])
    if locked_goal.mode == mode and previous_current is None:
        return locked_goal
    locked_goal.mode = mode
    locked_goal.save(update_fields=["mode"])
    event_type = (
        GoalActivityType.CURRENT_CHANGED
        if mode == GoalMode.AVAILABLE and previous_current
        else GoalActivityType.MODE_SELECTED
    )
    _record_goal_event(
        goal=locked_goal,
        event_type=event_type,
        description=(
            _("Current goal changed to %(title)s")
            if previous_current
            else _("Savings mode selected for %(title)s")
        )
        % {"title": locked_goal.title},
        actor=actor,
    )
    return locked_goal


@transaction.atomic
def add_saved_points(*, goal, child, amount, actor=None):
    if amount <= 0:
        raise ValidationError(_("Enter a positive point amount."))
    locked_child = ChildProfile.objects.select_for_update().get(
        pk=child.pk,
        is_active=True,
    )
    locked_goal = SavingsGoal.objects.select_for_update().get(
        pk=goal.pk,
        child=locked_child,
        status=GoalStatus.ACTIVE,
    )
    if locked_goal.mode != GoalMode.SAVED:
        raise ValidationError(_("Choose Save separately before adding points."))
    saved_amount = _active_saved_amount(locked_goal)
    remaining = locked_goal.target_amount - saved_amount
    if amount > remaining:
        raise ValidationError(
            _("You can add at most %(amount)s points to reach this goal.")
            % {"amount": max(remaining, 0)}
        )
    if locked_child.balance <= 0 or amount > locked_child.balance:
        raise ValidationError(_("You can save only points you currently have available."))
    contribution = SavingsContribution.objects.create(
        goal=locked_goal,
        amount=amount,
        state=SavingsContributionState.ACTIVE,
    )
    entry = post_ledger_entry(
        child=locked_child,
        delta=-amount,
        kind=LedgerKind.SAVINGS_TRANSFER,
        description=_("Saved for %(title)s") % {"title": locked_goal.title},
        actor=actor,
        source_id=contribution.pk,
    )
    contribution.ledger_entry = entry
    contribution.save(update_fields=["ledger_entry"])
    _record_goal_event(
        goal=locked_goal,
        event_type=GoalActivityType.TRANSFERRED,
        description=_("Saved %(amount)s points for %(title)s")
        % {"amount": amount, "title": locked_goal.title},
        actor=actor,
        amount=amount,
    )
    return contribution


@transaction.atomic
def request_goal_completion(*, goal, child):
    locked_child = ChildProfile.objects.select_for_update().get(
        pk=child.pk,
        is_active=True,
    )
    locked_goal = SavingsGoal.objects.select_for_update().get(
        pk=goal.pk,
        child=locked_child,
        status=GoalStatus.ACTIVE,
    )
    progress = (
        _active_saved_amount(locked_goal)
        if locked_goal.mode == GoalMode.SAVED
        else max(0, locked_child.balance)
        if locked_goal.mode == GoalMode.AVAILABLE
        else 0
    )
    if locked_goal.mode not in GoalMode.values or progress < locked_goal.target_amount:
        raise ValidationError(_("This goal has not reached its target yet."))
    if GoalCompletionRequest.objects.filter(
        goal=locked_goal, status=RequestStatus.PENDING
    ).exists():
        raise ValidationError(_("This goal is already waiting for parent approval."))
    try:
        with transaction.atomic():
            completion_request = GoalCompletionRequest.objects.create(goal=locked_goal)
    except IntegrityError as exc:
        raise ValidationError(
            _("This goal is already waiting for parent approval.")
        ) from exc
    _record_goal_event(
        goal=locked_goal,
        event_type=GoalActivityType.REACHED,
        description=_("Goal reached: %(title)s") % {"title": locked_goal.title},
    )
    return completion_request


@transaction.atomic
def approve_goal_completion(*, completion_request, actor):
    locked_request = GoalCompletionRequest.objects.select_for_update().get(
        pk=completion_request.pk
    )
    if locked_request.status != RequestStatus.PENDING:
        raise ValidationError(_("This goal request has already been resolved."))
    locked_goal = SavingsGoal.objects.select_for_update().get(
        pk=locked_request.goal_id,
        status=GoalStatus.ACTIVE,
    )
    locked_child = ChildProfile.objects.select_for_update().get(
        pk=locked_goal.child_id,
        is_active=True,
    )
    if locked_goal.mode == GoalMode.AVAILABLE:
        if locked_child.balance < locked_goal.target_amount:
            raise ValidationError(
                _("The goal cannot be completed because the available balance changed.")
            )
        post_ledger_entry(
            child=locked_child,
            delta=-locked_goal.target_amount,
            kind=LedgerKind.GOAL_COMPLETION,
            description=_("Completed goal: %(title)s") % {"title": locked_goal.title},
            actor=actor,
            source_id=locked_request.pk,
        )
    elif locked_goal.mode == GoalMode.SAVED:
        saved_contributions = list(
            SavingsContribution.objects.select_for_update().filter(
                goal=locked_goal,
                state=SavingsContributionState.ACTIVE,
            )
        )
        saved_amount = sum(contribution.amount for contribution in saved_contributions)
        if saved_amount < locked_goal.target_amount:
            raise ValidationError(_("The saved amount no longer reaches this goal."))
        now = timezone.now()
        SavingsContribution.objects.filter(
            pk__in=[contribution.pk for contribution in saved_contributions]
        ).update(state=SavingsContributionState.CONSUMED, resolved_at=now)
    else:
        raise ValidationError(_("Choose a savings mode before completing this goal."))
    locked_goal.status = GoalStatus.COMPLETED
    locked_goal.save(update_fields=["status"])
    locked_request.status = RequestStatus.APPROVED
    locked_request.decided_by = actor
    locked_request.decided_at = timezone.now()
    locked_request.save(update_fields=["status", "decided_by", "decided_at"])
    _record_goal_event(
        goal=locked_goal,
        event_type=GoalActivityType.COMPLETED,
        description=_("Goal completed: %(title)s") % {"title": locked_goal.title},
        actor=actor,
        amount=locked_goal.target_amount,
    )
    return locked_goal


@transaction.atomic
def keep_goal_active(*, completion_request, actor):
    locked_request = GoalCompletionRequest.objects.select_for_update().get(
        pk=completion_request.pk
    )
    if locked_request.status != RequestStatus.PENDING:
        raise ValidationError(_("This goal request has already been resolved."))
    locked_request.status = RequestStatus.REJECTED
    locked_request.decided_by = actor
    locked_request.decided_at = timezone.now()
    locked_request.save(update_fields=["status", "decided_by", "decided_at"])
    return locked_request


def _return_active_goal_points(*, goal, actor, require_contributions=False):
    contributions = list(
        SavingsContribution.objects.select_for_update().filter(
            goal=goal,
            state=SavingsContributionState.ACTIVE,
        )
        .order_by("created_at", "pk")
    )
    if not contributions and require_contributions:
        raise ValidationError(_("This goal has no saved points to return."))
    if not contributions:
        return 0
    locked_child = ChildProfile.objects.select_for_update().get(
        pk=goal.child_id,
        is_active=True,
    )
    total = sum(contribution.amount for contribution in contributions)
    now = timezone.now()
    for contribution in contributions:
        post_ledger_entry(
            child=locked_child,
            delta=contribution.amount,
            kind=LedgerKind.SAVINGS_RETURN,
            description=_("Returned from %(title)s") % {"title": goal.title},
            actor=actor,
            source_id=contribution.pk,
        )
        contribution.state = SavingsContributionState.RETURNED
        contribution.resolved_at = now
        contribution.save(update_fields=["state", "resolved_at"])
    return total


@transaction.atomic
def return_saved_points(*, goal, actor):
    locked_goal = SavingsGoal.objects.select_for_update().get(
        pk=goal.pk,
        status=GoalStatus.ACTIVE,
    )
    if locked_goal.mode != GoalMode.SAVED:
        raise ValidationError(_("Only separately saved points can be returned."))
    total = _return_active_goal_points(
        goal=locked_goal,
        actor=actor,
        require_contributions=True,
    )
    _record_goal_event(
        goal=locked_goal,
        event_type=GoalActivityType.RETURNED,
        description=_("Returned %(amount)s points from %(title)s")
        % {"amount": total, "title": locked_goal.title},
        actor=actor,
        amount=total,
    )
    return total


@transaction.atomic
def update_savings_goal(*, goal, title, target_amount, icon, actor):
    if target_amount <= 0:
        raise ValidationError(_("The goal target must be greater than zero."))
    locked_goal = SavingsGoal.objects.select_for_update().get(pk=goal.pk)
    saved_amount = _active_saved_amount(locked_goal)
    if target_amount < saved_amount:
        raise ValidationError(
            _("Return the excess saved points before lowering this target.")
        )
    locked_goal.title = title.strip()
    locked_goal.target_amount = target_amount
    locked_goal.icon = icon
    locked_goal.save(update_fields=["title", "target_amount", "icon"])
    return locked_goal


@transaction.atomic
def close_savings_goal(*, goal, actor):
    locked_goal = SavingsGoal.objects.select_for_update().get(
        pk=goal.pk,
        status=GoalStatus.ACTIVE,
    )
    if _active_saved_amount(locked_goal):
        raise ValidationError(_("Return saved points before closing this goal."))
    GoalCompletionRequest.objects.filter(
        goal=locked_goal,
        status=RequestStatus.PENDING,
    ).update(
        status=RequestStatus.CANCELLED,
        decided_by=actor,
        decided_at=timezone.now(),
    )
    locked_goal.status = GoalStatus.CANCELLED
    locked_goal.save(update_fields=["status"])
    _record_goal_event(
        goal=locked_goal,
        event_type=GoalActivityType.CLOSED,
        description=_("Goal closed: %(title)s") % {"title": locked_goal.title},
        actor=actor,
    )
    return locked_goal


@transaction.atomic
def delete_savings_goal(*, goal, actor):
    locked_goal = SavingsGoal.objects.select_for_update().get(
        pk=goal.pk,
        status=GoalStatus.ACTIVE,
    )
    returned_amount = _return_active_goal_points(
        goal=locked_goal,
        actor=actor,
    )
    GoalCompletionRequest.objects.filter(
        goal=locked_goal,
        status=RequestStatus.PENDING,
    ).update(
        status=RequestStatus.CANCELLED,
        decided_by=actor,
        decided_at=timezone.now(),
    )
    locked_goal.status = GoalStatus.CANCELLED
    locked_goal.mode = None
    locked_goal.save(update_fields=["status", "mode"])
    if returned_amount:
        description = _(
            "Goal deleted: %(title)s · %(amount)s points returned"
        ) % {"title": locked_goal.title, "amount": returned_amount}
    else:
        description = _("Goal deleted: %(title)s") % {"title": locked_goal.title}
    _record_goal_event(
        goal=locked_goal,
        event_type=GoalActivityType.CLOSED,
        description=description,
        actor=actor,
        amount=returned_amount or None,
    )
    return locked_goal, returned_amount


def submit_reward_request(*, child, reward):
    if not reward.is_active:
        raise ValidationError(_("This reward is no longer active."))
    try:
        with transaction.atomic():
            locked_child = ChildProfile.objects.select_for_update().get(pk=child.pk)
            if assigned_tasks_block_rewards(locked_child):
                raise ValidationError(
                    _(
                        "Complete the assigned tasks before requesting a new reward."
                    )
                )
            if reward_requests_blocked(locked_child):
                raise ValidationError(
                    _(
                        "New reward requests are paused after half of the credit limit is used. "
                        "They will be available again when the balance improves."
                    )
                )
            if not reward_is_affordable(locked_child, reward):
                raise ValidationError(
                    _("You do not have enough points for this reward.")
                )
            return RewardRequest.objects.create(
                child=locked_child,
                reward=reward,
                reward_title=reward.title,
                cost_snapshot=reward.cost,
            )
    except IntegrityError as exc:
        raise ValidationError(_("This reward is already awaiting approval.")) from exc


@transaction.atomic
def approve_reward_request(*, request, actor):
    locked = RewardRequest.objects.select_related("child").get(pk=request.pk)
    if locked.status != RequestStatus.PENDING:
        raise ValidationError(_("This request has already been resolved."))
    decided_at = timezone.now()
    claimed = RewardRequest.objects.filter(
        pk=locked.pk,
        status=RequestStatus.PENDING,
    ).update(
        status=RequestStatus.APPROVED,
        decided_by=actor,
        decided_at=decided_at,
    )
    if not claimed:
        raise ValidationError(_("This request has already been resolved."))
    entry = post_ledger_entry(
        child=locked.child,
        delta=-locked.cost_snapshot,
        kind=LedgerKind.REWARD,
        description=locked.reward_title,
        actor=actor,
        source_id=locked.pk,
        enforce_limit=True,
    )
    return entry


@transaction.atomic
def approve_proposal(*, proposal, actor, final_cost, goal_mode=None):
    locked = Proposal.objects.select_related("child").get(pk=proposal.pk)
    if locked.status != RequestStatus.PENDING:
        raise ValidationError(_("This proposal has already been resolved."))
    if final_cost <= 0:
        raise ValidationError(_("The cost must be greater than zero."))
    selected_goal_mode = None
    if locked.proposal_type == ProposalType.REWARD:
        goal_mode_value = None
    else:
        selected_goal_mode = locked.goal_mode or goal_mode
        if selected_goal_mode not in GoalMode.values:
            raise ValidationError(_("Choose how this savings goal should save points."))
        goal_mode_value = selected_goal_mode
    decided_at = timezone.now()
    claimed = Proposal.objects.filter(
        pk=locked.pk,
        status=RequestStatus.PENDING,
    ).update(
        status=RequestStatus.APPROVED,
        final_cost=final_cost,
        goal_mode=goal_mode_value,
        decided_by=actor,
        decided_at=decided_at,
    )
    if not claimed:
        raise ValidationError(_("This proposal has already been resolved."))
    if locked.proposal_type == ProposalType.REWARD:
        created = Reward.objects.create(title=locked.title, icon=locked.icon, cost=final_cost)
    else:
        created = create_savings_goal(
            child=locked.child,
            title=locked.title,
            target_amount=final_cost,
            icon=locked.icon,
            actor=actor,
            mode=selected_goal_mode,
        )
    return created


@transaction.atomic
def reject_reward_request(*, request, actor, reason):
    decided_at = timezone.now()
    claimed = RewardRequest.objects.filter(
        pk=request.pk,
        status=RequestStatus.PENDING,
    ).update(
        status=RequestStatus.REJECTED,
        rejection_reason=reason.strip(),
        decided_by=actor,
        decided_at=decided_at,
    )
    if not claimed:
        raise ValidationError(_("This request has already been resolved."))
    return RewardRequest.objects.get(pk=request.pk)


@transaction.atomic
def reject_proposal(*, proposal, actor, reason):
    claimed = Proposal.objects.filter(
        pk=proposal.pk,
        status=RequestStatus.PENDING,
    ).update(
        status=RequestStatus.REJECTED,
        parent_note=reason.strip(),
        decided_by=actor,
        decided_at=timezone.now(),
    )
    if not claimed:
        raise ValidationError(_("This proposal has already been resolved."))
    return Proposal.objects.get(pk=proposal.pk)


@transaction.atomic
def cancel_reward_request(*, request, child):
    return bool(
        RewardRequest.objects.filter(
            pk=request.pk,
            child=child,
            status=RequestStatus.PENDING,
        ).update(
            status=RequestStatus.CANCELLED,
            decided_at=timezone.now(),
        )
    )
