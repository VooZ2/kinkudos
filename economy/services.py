import random

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import (
    BirthdayAward,
    ChildProfile,
    FamilySettings,
    GoalStatus,
    LedgerEntry,
    LedgerKind,
    PointGift,
    Proposal,
    ProposalType,
    RequestStatus,
    Reward,
    RewardRequest,
    SavingsGoal,
    Task,
    TaskClaim,
    Theme,
)


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


def submit_task(*, child, task, photo_bonus_snapshot=0):
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
            )
    except IntegrityError as exc:
        raise ValidationError(_("This task is already awaiting approval.")) from exc


@transaction.atomic
def approve_task_claim(*, claim, actor):
    locked = TaskClaim.objects.select_for_update().select_related("child").get(pk=claim.pk)
    if locked.status != RequestStatus.PENDING:
        raise ValidationError(_("This request has already been resolved."))
    entry = post_ledger_entry(
        child=locked.child,
        delta=locked.total_reward,
        kind=LedgerKind.TASK,
        description=locked.task_title,
        actor=actor,
        source_id=locked.pk,
    )
    locked.status = RequestStatus.APPROVED
    locked.decided_by = actor
    locked.decided_at = timezone.now()
    locked.save(update_fields=["status", "decided_by", "decided_at"])
    return entry


def reject_task_claim(*, claim, actor, reason):
    with transaction.atomic():
        locked = TaskClaim.objects.select_for_update().get(pk=claim.pk)
        if locked.status != RequestStatus.PENDING:
            raise ValidationError(_("This request has already been resolved."))
        locked.status = RequestStatus.REJECTED
        locked.rejection_reason = reason.strip()
        locked.decided_by = actor
        locked.decided_at = timezone.now()
        locked.save(
            update_fields=["status", "rejection_reason", "decided_by", "decided_at"]
        )
    return locked


def request_task_revision(*, claim, actor, reason):
    with transaction.atomic():
        locked = TaskClaim.objects.select_for_update().get(pk=claim.pk)
        if locked.status != RequestStatus.PENDING:
            raise ValidationError(_("This request has already been resolved."))
        locked.status = RequestStatus.NEEDS_CHANGES
        locked.revision_note = reason.strip()
        locked.decided_by = actor
        locked.decided_at = timezone.now()
        locked.save(
            update_fields=[
                "status",
                "revision_note",
                "decided_by",
                "decided_at",
            ]
        )
    return locked


def resubmit_task_claim(*, claim):
    with transaction.atomic():
        locked = TaskClaim.objects.select_for_update().get(pk=claim.pk)
        if locked.status != RequestStatus.NEEDS_CHANGES:
            raise ValidationError(_("This task is not awaiting corrections."))
        locked.status = RequestStatus.PENDING
        locked.revision_note = ""
        locked.decided_by = None
        locked.decided_at = None
        locked.submitted_at = timezone.now()
        locked.save(
            update_fields=[
                "status",
                "revision_note",
                "decided_by",
                "decided_at",
                "submitted_at",
            ]
        )
    return locked


def reward_requests_blocked(child):
    credit_limit = abs(min(child.min_balance, 0))
    if credit_limit == 0:
        return False
    used_credit = max(0, -child.balance)
    return used_credit * 2 >= credit_limit


def reward_is_affordable(child, reward):
    return child.balance - reward.cost >= child.min_balance


def submit_reward_request(*, child, reward):
    if not reward.is_active:
        raise ValidationError(_("This reward is no longer active."))
    try:
        with transaction.atomic():
            locked_child = ChildProfile.objects.select_for_update().get(pk=child.pk)
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
    locked = RewardRequest.objects.select_for_update().select_related("child").get(pk=request.pk)
    if locked.status != RequestStatus.PENDING:
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
    locked.status = RequestStatus.APPROVED
    locked.decided_by = actor
    locked.decided_at = timezone.now()
    locked.save(update_fields=["status", "decided_by", "decided_at"])
    return entry


@transaction.atomic
def approve_proposal(*, proposal, actor, final_cost):
    locked = Proposal.objects.select_for_update().select_related("child").get(pk=proposal.pk)
    if locked.status != RequestStatus.PENDING:
        raise ValidationError(_("This proposal has already been resolved."))
    if final_cost <= 0:
        raise ValidationError(_("The cost must be greater than zero."))
    if locked.proposal_type == ProposalType.REWARD:
        created = Reward.objects.create(title=locked.title, icon=locked.icon, cost=final_cost)
    else:
        created = SavingsGoal.objects.create(
            child=locked.child,
            title=locked.title,
            icon=locked.icon,
            target_amount=final_cost,
            status=GoalStatus.ACTIVE,
        )
    locked.status = RequestStatus.APPROVED
    locked.final_cost = final_cost
    locked.decided_by = actor
    locked.decided_at = timezone.now()
    locked.save(update_fields=["status", "final_cost", "decided_by", "decided_at"])
    return created
