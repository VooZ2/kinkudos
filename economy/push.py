import json
import logging

from django.conf import settings
from django.utils.translation import gettext as _
from pywebpush import WebPushException, webpush

from .models import PushSubscription
from .templatetags.economy_tags import currency_unit, theme_text

logger = logging.getLogger(__name__)


def _currency_amount(value, child):
    return f"{value} {currency_unit(value, child.theme)}"


def _send(payload, subscriptions):
    if not settings.VAPID_PRIVATE_KEY:
        return
    data = json.dumps(payload)
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                },
                data=data,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_SUBJECT},
                ttl=86400,
            )
        except WebPushException as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code in {404, 410}:
                subscription.delete()
            else:
                logger.warning("Could not send Web Push: %s", exc)
        except Exception:
            # Push is optional; provider or key failures must never turn an
            # already-saved request into an HTTP 500 response.
            logger.exception("Unexpected Web Push error")


def notify_task_claim(claim):
    _send(
        {
            "title": _("A new task is awaiting approval"),
            "body": f"{claim.child.name}: {claim.task_title} (+{claim.total_reward})",
            "url": "/tevai/",
            "tag": f"task-claim-{claim.pk}",
        },
        PushSubscription.objects.filter(user__isnull=False),
    )


def notify_reward_request(reward_request):
    _send(
        {
            "title": _("A reward is awaiting approval"),
            "body": f"{reward_request.child.name}: {reward_request.reward_title}",
            "url": "/tevai/",
            "tag": f"reward-request-{reward_request.pk}",
        },
        PushSubscription.objects.filter(user__isnull=False),
    )


def notify_proposal(proposal):
    _send(
        {
            "title": _("A new suggestion is awaiting approval"),
            "body": f"{proposal.child.name}: {proposal.title}",
            "url": "/tevai/",
            "tag": f"proposal-{proposal.pk}",
        },
        PushSubscription.objects.filter(user__isnull=False),
    )


def notify_birth_date_change(change):
    _send(
        {
            "title": _("A birthday change is awaiting approval"),
            "body": change.child.name,
            "url": "/tevai/",
            "tag": f"birthday-change-{change.pk}",
        },
        PushSubscription.objects.filter(user__isnull=False),
    )


def notify_assigned_tasks(batch):
    _send(
        {
            "title": str(theme_text(batch.child.theme, "assigned_title")),
            "body": str(theme_text(batch.child.theme, "assigned_help")),
            "url": "/vaikas/mano/#paskirti-darbai",
            "tag": f"assigned-tasks-{batch.pk}",
        },
        PushSubscription.objects.filter(child=batch.child),
    )


def notify_task_revision(claim):
    body = claim.task_title
    if claim.revision_note:
        body = f"{body}: {claim.revision_note}"
    _send(
        {
            "title": _("A task needs a little more work"),
            "body": body,
            "url": "/vaikas/mano/#darbai",
            "tag": f"task-revision-{claim.pk}",
        },
        PushSubscription.objects.filter(child=claim.child),
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
            "url": "/vaikas/mano/#darbai",
            "tag": f"task-{state}-{claim.pk}",
        },
        PushSubscription.objects.filter(child=claim.child),
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
            "url": "/vaikas/mano/#prizai",
            "tag": f"reward-{state}-{reward_request.pk}",
        },
        PushSubscription.objects.filter(child=reward_request.child),
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
            "url": "/vaikas/mano/#prizai",
            "tag": f"proposal-{state}-{proposal.pk}",
        },
        PushSubscription.objects.filter(child=proposal.child),
    )


def notify_birth_date_decision(change, *, approved):
    _send(
        {
            "title": _("Your birthday change was approved")
            if approved
            else _("Your birthday change was rejected"),
            "body": "",
            "url": "/vaikas/mano/#profilis",
            "tag": f"birthday-change-{'approved' if approved else 'rejected'}-{change.pk}",
        },
        PushSubscription.objects.filter(child=change.child),
    )


def notify_gift_received(gift):
    _send(
        {
            "title": _("You received a gift!"),
            "body": _("%(name)s gave you %(currency)s.") % {
                "name": gift.sender.name,
                "currency": currency_unit(10, gift.recipient.theme),
            },
            "url": "/vaikas/mano/#istorija",
            "tag": f"point-gift-{gift.pk}",
        },
        PushSubscription.objects.filter(child=gift.recipient),
    )


def notify_birthday_award(award):
    _send(
        {
            "title": _("Happy birthday!"),
            "body": _("You received %(amount)s for your birthday") % {
                "amount": _currency_amount(award.points, award.child),
            },
            "url": "/vaikas/mano/#istorija",
            "tag": f"birthday-award-{award.pk}",
        },
        PushSubscription.objects.filter(child=award.child),
    )


def notify_lottery_reminder(child):
    from .models import FamilySettings

    ticket_cost = FamilySettings.load().lottery_ticket_cost
    _send(
        {
            "title": str(theme_text(child.theme, "lottery_title")),
            "body": str(
                _(
                    "You have not bought a scratch ticket this week. It costs %(cost)s "
                    "and you may win, get nothing, or lose points."
                )
                % {"cost": _currency_amount(ticket_cost, child)}
            ),
            "url": "/vaikas/mano/#prizai",
            "tag": f"lottery-reminder-{child.pk}",
        },
        PushSubscription.objects.filter(child=child),
    )
