import random
from collections import Counter
from datetime import datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import (
    ChildProfile,
    FamilySettings,
    LedgerKind,
    LotteryReminder,
    LotteryTicket,
    LotteryTicketStatus,
    PushSubscription,
)
from .services import (
    assigned_tasks_block_rewards,
    post_ledger_entry,
    reward_requests_blocked,
)

LOTTERY_JACKPOT_AFTER = 11


def lottery_week_start(current_date=None):
    current_date = current_date or timezone.localdate()
    return current_date - timedelta(days=current_date.weekday())


def _weighted_range(rng, ranges):
    roll = rng.randrange(100)
    cumulative = 0
    for weight, lower, upper in ranges:
        cumulative += weight
        if roll < cumulative:
            return rng.randint(lower, upper)
    raise RuntimeError("Lottery weights must add up to 100.")


def _draw_prize(child, rng):
    recent_prizes = list(
        child.lottery_tickets.order_by("-purchased_at", "-pk").values_list(
            "prize_amount", flat=True
        )[:LOTTERY_JACKPOT_AFTER]
    )
    jackpot_due = (
        len(recent_prizes) == LOTTERY_JACKPOT_AFTER
        and not any(prize >= 101 for prize in recent_prizes)
    )
    if jackpot_due:
        return rng.randint(101, 150)

    outcome_roll = rng.randrange(100)
    if outcome_roll < 50:
        return _weighted_range(
            rng,
            (
                (70, 1, 67),
                (25, 68, 100),
                (5, 101, 150),
            ),
        )
    if outcome_roll < 80:
        return -_weighted_range(
            rng,
            (
                (80, 1, 20),
                (20, 21, 50),
            ),
        )
    return 0


def _draw_filler_value(rng, counts, excluded=None):
    excluded = excluded or set()
    while True:
        value = rng.randint(-50, 150)
        if value == 0 or value in excluded or counts[value] >= 2:
            continue
        return value


def _draw_board(prize_amount, rng):
    values = []
    counts = Counter()
    if prize_amount:
        values.extend([prize_amount] * 3)
        counts[prize_amount] = 3
    while len(values) < 9:
        value = _draw_filler_value(
            rng,
            counts,
            excluded={prize_amount} if prize_amount else None,
        )
        values.append(value)
        counts[value] += 1
    rng.shuffle(values)
    return values


def lottery_state(child, current_date=None, family_settings=None):
    family_settings = family_settings or FamilySettings.load()
    ticket_cost = family_settings.lottery_ticket_cost
    weekly_limit = family_settings.lottery_weekly_limit
    feature_enabled = family_settings.lottery_enabled and child.lottery_enabled
    week_start = lottery_week_start(current_date)
    tickets_used = child.lottery_tickets.filter(week_start=week_start).count()
    open_ticket = child.lottery_tickets.filter(
        status=LotteryTicketStatus.OPEN
    ).first()
    block_reason = ""
    if open_ticket:
        block_reason = "open"
    elif not feature_enabled:
        block_reason = "disabled"
    elif tickets_used >= weekly_limit:
        block_reason = "weekly_limit"
    elif assigned_tasks_block_rewards(child):
        block_reason = "assigned_tasks"
    elif reward_requests_blocked(child):
        block_reason = "credit_paused"
    elif child.balance < ticket_cost:
        block_reason = "balance"
    return {
        "open_ticket": open_ticket,
        "tickets_used": tickets_used,
        "tickets_remaining": max(weekly_limit - tickets_used, 0),
        "ticket_cost": ticket_cost,
        "weekly_limit": weekly_limit,
        "feature_enabled": feature_enabled,
        "is_visible": feature_enabled or bool(open_ticket),
        "can_purchase": not block_reason,
        "block_reason": block_reason,
        "week_start": week_start,
    }


@transaction.atomic
def purchase_lottery_ticket(*, child, rng=None, current_date=None):
    rng = rng or random.SystemRandom()
    locked_child = ChildProfile.objects.select_for_update().get(
        pk=child.pk,
        is_active=True,
    )
    state = lottery_state(locked_child, current_date)
    errors = {
        "open": _("Finish your open lottery ticket before buying another."),
        "disabled": _("Lottery tickets are disabled."),
        "weekly_limit": _(
            "You have already used all %(limit)s lottery tickets this week."
        )
        % {"limit": state["weekly_limit"]},
        "assigned_tasks": _(
            "Complete the assigned tasks before buying a lottery ticket."
        ),
        "credit_paused": _(
            "Lottery tickets are paused until your point balance improves."
        ),
        "balance": _(
            "A lottery ticket can be bought only with %(cost)s points you have earned."
        )
        % {"cost": state["ticket_cost"]},
    }
    if state["block_reason"]:
        raise ValidationError(errors[state["block_reason"]])

    prize_amount = _draw_prize(locked_child, rng)
    ticket = LotteryTicket.objects.create(
        child=locked_child,
        week_start=state["week_start"],
        values=_draw_board(prize_amount, rng),
        prize_amount=prize_amount,
    )
    purchase_entry = post_ledger_entry(
        child=locked_child,
        delta=-state["ticket_cost"],
        kind=LedgerKind.LOTTERY,
        description=_("Lottery ticket"),
        source_id=ticket.pk,
    )
    ticket.purchase_ledger_entry = purchase_entry
    ticket.save(update_fields=["purchase_ledger_entry"])
    return ticket


@transaction.atomic
def reveal_lottery_ticket(*, ticket, child):
    locked_child = ChildProfile.objects.select_for_update().get(
        pk=child.pk,
        is_active=True,
    )
    locked_ticket = LotteryTicket.objects.select_for_update().get(
        pk=ticket.pk,
        child=locked_child,
    )
    if locked_ticket.status == LotteryTicketStatus.REVEALED:
        return locked_ticket

    applied_delta = locked_ticket.prize_amount
    if applied_delta < 0:
        applied_delta = min(
            0,
            max(
                applied_delta,
                locked_child.min_balance - locked_child.balance,
            ),
        )
    result_entry = post_ledger_entry(
        child=locked_child,
        delta=applied_delta,
        kind=LedgerKind.LOTTERY,
        description=_("Lottery result"),
        source_id=locked_ticket.pk,
    )
    locked_ticket.applied_delta = applied_delta
    locked_ticket.result_ledger_entry = result_entry
    locked_ticket.status = LotteryTicketStatus.REVEALED
    locked_ticket.revealed_at = timezone.now()
    locked_ticket.save(
        update_fields=[
            "applied_delta",
            "result_ledger_entry",
            "status",
            "revealed_at",
        ]
    )
    return locked_ticket


def _random_reminder_time(week_start, rng):
    day_offset = rng.choice((3, 4, 5, 6))
    start_hour = 16 if day_offset in {3, 4} else 10
    slot = rng.randrange((20 - start_hour) * 2)
    reminder_time = time(
        hour=start_hour + slot // 2,
        minute=30 if slot % 2 else 0,
    )
    naive = datetime.combine(week_start + timedelta(days=day_offset), reminder_time)
    return timezone.make_aware(naive, timezone.get_current_timezone())


def send_due_lottery_reminders(*, current_time=None, rng=None):
    from .push import notify_lottery_reminder

    current_time = current_time or timezone.now()
    rng = rng or random.SystemRandom()
    local_date = timezone.localtime(current_time).date()
    week_start = lottery_week_start(local_date)
    family_settings = FamilySettings.load()
    if not family_settings.lottery_enabled:
        return []
    child_ids = (
        ChildProfile.objects.filter(
            is_active=True,
            lottery_enabled=True,
            push_subscriptions__isnull=False,
        )
        .distinct()
        .values_list("pk", flat=True)
    )
    sent = []
    for child_id in child_ids:
        reminder, _created = LotteryReminder.objects.get_or_create(
            child_id=child_id,
            week_start=week_start,
            defaults={
                "scheduled_for": _random_reminder_time(week_start, rng),
            },
        )
        if reminder.handled_at or reminder.scheduled_for > current_time:
            continue
        eligible = False
        with transaction.atomic():
            reminder = LotteryReminder.objects.select_for_update().get(pk=reminder.pk)
            if reminder.handled_at:
                continue
            child = ChildProfile.objects.select_for_update().get(pk=child_id)
            eligible = (
                child.balance >= max(50, family_settings.lottery_ticket_cost)
                and not child.lottery_tickets.filter(week_start=week_start).exists()
                and not assigned_tasks_block_rewards(child)
                and not reward_requests_blocked(child)
                and PushSubscription.objects.filter(child=child).exists()
            )
            reminder.sent = eligible
            reminder.handled_at = current_time
            reminder.save(update_fields=["sent", "handled_at"])
        if eligible:
            notify_lottery_reminder(child)
            sent.append(child)
    return sent
