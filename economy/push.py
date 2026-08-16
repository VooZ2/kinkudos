import json
import logging
import threading

from django.conf import settings
from django.db import close_old_connections, transaction
from django.urls import reverse
from django.utils.translation import gettext as _
from pywebpush import WebPushException, webpush

from .models import PushSubscription
from .templatetags.economy_tags import currency_unit, theme_text

logger = logging.getLogger(__name__)


def _currency_amount(value, child):
    return f"{value} {currency_unit(value, child.theme)}"


def _parent_dashboard_url():
    return reverse("parent_dashboard")


def _child_dashboard_url(fragment):
    return f"{reverse('child_dashboard')}#{fragment}"


def _parent_subscriptions():
    return PushSubscription.objects.filter(
        user__isnull=False,
        user__is_active=True,
        user__caregiver_profile__isnull=True,
    )


def _child_subscriptions(child):
    return PushSubscription.objects.filter(child=child, child__is_active=True)


def _deliver_webpush(data, subscription_rows):
    close_old_connections()
    try:
        for row in subscription_rows:
            try:
                webpush(
                    subscription_info={
                        "endpoint": row["endpoint"],
                        "keys": {"p256dh": row["p256dh"], "auth": row["auth"]},
                    },
                    data=data,
                    vapid_private_key=settings.VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": settings.VAPID_SUBJECT},
                    ttl=86400,
                    # Never block a request worker forever on a blackholed push endpoint.
                    timeout=10,
                )
            except WebPushException as exc:
                status_code = getattr(getattr(exc, "response", None), "status_code", None)
                if status_code in {404, 410}:
                    PushSubscription.objects.filter(pk=row["pk"]).delete()
                else:
                    logger.warning("Could not send Web Push: %s", exc)
            except Exception:
                # Push is optional; provider or key failures must never turn an
                # already-saved request into an HTTP 500 response.
                logger.exception("Unexpected Web Push error")
    finally:
        close_old_connections()


def _start_push_thread(target, args):
    threading.Thread(target=target, args=args, daemon=True).start()


def _send(payload, subscriptions):
    if not settings.VAPID_PRIVATE_KEY:
        return
    subscription_rows = list(
        subscriptions.values("pk", "endpoint", "p256dh", "auth")
    )
    if not subscription_rows:
        return
    data = json.dumps(payload)

    def deliver():
        _start_push_thread(_deliver_webpush, (data, subscription_rows))

    transaction.on_commit(deliver)


def notify_task_claim(claim):
    _send(
        {
            "title": _("A new task is awaiting approval"),
            "body": f"{claim.child.name}: {claim.task_title} (+{claim.total_reward})",
            "url": _parent_dashboard_url(),
            "tag": f"task-claim-{claim.pk}",
        },
        _parent_subscriptions(),
    )


def notify_reward_request(reward_request):
    _send(
        {
            "title": _("A reward is awaiting approval"),
            "body": f"{reward_request.child.name}: {reward_request.reward_title}",
            "url": _parent_dashboard_url(),
            "tag": f"reward-request-{reward_request.pk}",
        },
        _parent_subscriptions(),
    )


def notify_proposal(proposal):
    _send(
        {
            "title": _("A new suggestion is awaiting approval"),
            "body": f"{proposal.child.name}: {proposal.title}",
            "url": _parent_dashboard_url(),
            "tag": f"proposal-{proposal.pk}",
        },
        _parent_subscriptions(),
    )


def notify_birth_date_change(change):
    _send(
        {
            "title": _("A birthday change is awaiting approval"),
            "body": change.child.name,
            "url": _parent_dashboard_url(),
            "tag": f"birthday-change-{change.pk}",
        },
        _parent_subscriptions(),
    )


def notify_assigned_tasks(batch):
    _send(
        {
            "title": str(theme_text(batch.child.theme, "assigned_title")),
            "body": str(theme_text(batch.child.theme, "assigned_help")),
            "url": _child_dashboard_url("paskirti-darbai"),
            "tag": f"assigned-tasks-{batch.pk}",
        },
        _child_subscriptions(batch.child),
    )


def notify_assigned_tasks_nudge(batch):
    _send(
        {
            "title": str(theme_text(batch.child.theme, "assigned_nudge_title")),
            "body": str(theme_text(batch.child.theme, "assigned_nudge_help")),
            "url": _child_dashboard_url("paskirti-darbai"),
            "tag": f"assigned-tasks-nudge-{batch.pk}",
        },
        _child_subscriptions(batch.child),
    )


def notify_assigned_task_completed(assigned_task):
    child = assigned_task.batch.child
    _send(
        {
            "title": _("An assigned task was completed"),
            "body": (
                f"{child.name}: {assigned_task.title_snapshot} "
                f"(+{_currency_amount(assigned_task.reward_snapshot, child)})"
            ),
            "url": f"{_parent_dashboard_url()}#parent-history",
            "tag": f"assigned-task-completed-{assigned_task.pk}",
        },
        _parent_subscriptions(),
    )


def notify_task_revision(claim):
    body = claim.task_title
    if claim.revision_note:
        body = f"{body}: {claim.revision_note}"
    _send(
        {
            "title": _("A task needs a little more work"),
            "body": body,
            "url": _child_dashboard_url("darbai"),
            "tag": f"task-revision-{claim.pk}",
        },
        _child_subscriptions(claim.child),
    )


def notify_task_decision(claim, *, approved):
    if approved:
        title = _("Your task was approved")
        body = _("%(task)s: +%(amount)s") % {
            "task": claim.task_title,
            "amount": _currency_amount(claim.total_reward, claim.child),
        }
        state = "approved"
    else:
        title = _("Your task was rejected")
        body = claim.task_title
        if claim.rejection_reason:
            body = f"{body}: {claim.rejection_reason}"
        state = "rejected"
    _send(
        {
            "title": title,
            "body": body,
            "url": _child_dashboard_url("darbai"),
            "tag": f"task-{state}-{claim.pk}",
        },
        _child_subscriptions(claim.child),
    )


def notify_reward_decision(reward_request, *, approved):
    if approved:
        title = _("Your reward was approved")
        body = reward_request.reward_title
        state = "approved"
    else:
        title = _("Your reward request was rejected")
        body = reward_request.reward_title
        if reward_request.rejection_reason:
            body = f"{body}: {reward_request.rejection_reason}"
        state = "rejected"
    _send(
        {
            "title": title,
            "body": body,
            "url": _child_dashboard_url("prizai"),
            "tag": f"reward-{state}-{reward_request.pk}",
        },
        _child_subscriptions(reward_request.child),
    )


def notify_proposal_decision(proposal, *, approved):
    if approved:
        title = _("Your suggestion was approved")
        body = proposal.title
        state = "approved"
    else:
        title = _("Your suggestion was rejected")
        body = proposal.title
        if proposal.parent_note:
            body = f"{body}: {proposal.parent_note}"
        state = "rejected"
    _send(
        {
            "title": title,
            "body": body,
            "url": _child_dashboard_url("prizai"),
            "tag": f"proposal-{state}-{proposal.pk}",
        },
        _child_subscriptions(proposal.child),
    )


def notify_birth_date_decision(change, *, approved):
    _send(
        {
            "title": _("Your birthday change was approved")
            if approved
            else _("Your birthday change was rejected"),
            "body": "",
            "url": _child_dashboard_url("profilis"),
            "tag": f"birthday-change-{'approved' if approved else 'rejected'}-{change.pk}",
        },
        _child_subscriptions(change.child),
    )


def notify_gift_received(gift):
    _send(
        {
            "title": _("You received a gift!"),
            "body": _("%(name)s gave you %(currency)s.") % {
                "name": gift.sender.name,
                "currency": currency_unit(10, gift.recipient.theme),
            },
            "url": _child_dashboard_url("istorija"),
            "tag": f"point-gift-{gift.pk}",
        },
        _child_subscriptions(gift.recipient),
    )


def notify_birthday_award(award):
    _send(
        {
            "title": _("Happy birthday!"),
            "body": _("You received %(amount)s for your birthday") % {
                "amount": _currency_amount(award.points, award.child),
            },
            "url": _child_dashboard_url("istorija"),
            "tag": f"birthday-award-{award.pk}",
        },
        _child_subscriptions(award.child),
    )


def notify_lottery_reminder(child):
    from .models import FamilySettings

    ticket_cost = FamilySettings.load().lottery_ticket_cost
    _send(
        {
            "title": str(theme_text(child.theme, "lottery_title")),
            "body": str(
                _(
                    "You have not bought a surprise card this week. It costs %(cost)s. "
                    "Your points may go up, stay the same, or go down."
                )
                % {"cost": _currency_amount(ticket_cost, child)}
            ),
            "url": _child_dashboard_url("prizai"),
            "tag": f"lottery-reminder-{child.pk}",
        },
        _child_subscriptions(child),
    )
