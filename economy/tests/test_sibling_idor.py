import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from economy.models import (
    ChildProfile,
    GoalMode,
    GoalStatus,
    LedgerKind,
    LotteryTicket,
    LotteryTicketStatus,
    RequestStatus,
    SavingsGoal,
    Task,
    TaskClaim,
)
from economy.services import post_ledger_entry


@override_settings(LANGUAGE_CODE="en")
class SiblingIdorMatrixTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user(
            "idor-parent",
            password="Safe-idor-parent-123!",
            is_staff=True,
        )
        self.actor = ChildProfile(name="Actor", theme_selected=True, balance=50)
        self.actor.set_pin("1111")
        self.actor.save()
        self.owner = ChildProfile(name="Owner", theme_selected=True, balance=80)
        self.owner.set_pin("2222")
        self.owner.save()

        self.task = Task.objects.create(title="Owner task", reward=10)
        self.claim = TaskClaim.objects.create(
            child=self.owner,
            task=self.task,
            task_title=self.task.title,
            reward_snapshot=self.task.reward,
            status=RequestStatus.NEEDS_CHANGES,
            rejection_reason="Need a clearer photo",
        )
        self.ticket = LotteryTicket.objects.create(
            child=self.owner,
            week_start=timezone.localdate(),
            values=[3, 1, 3, 2, 3, 4, 5, 6, 7],
            prize_amount=3,
            status=LotteryTicketStatus.OPEN,
        )
        self.goal = SavingsGoal.objects.create(
            child=self.owner,
            title="Owner goal",
            target_amount=25,
            mode=GoalMode.SAVED,
        )

    def login_as(self, child):
        session = self.client.session
        session["child_id"] = child.pk
        session.save()

    def test_sibling_cannot_reveal_lottery_ticket(self):
        self.login_as(self.actor)
        response = self.client.post(
            reverse("child_reveal_lottery_ticket", args=[self.ticket.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 404)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, LotteryTicketStatus.OPEN)
        self.assertIsNone(self.ticket.revealed_at)

    def test_sibling_cannot_add_points_to_other_goal(self):
        self.login_as(self.actor)
        before_actor = self.actor.balance
        before_owner = self.owner.balance
        response = self.client.post(
            reverse("child_add_goal_points", args=[self.goal.pk]),
            {"amount": 5},
        )
        self.assertEqual(response.status_code, 404)
        self.actor.refresh_from_db()
        self.owner.refresh_from_db()
        self.goal.refresh_from_db()
        self.assertEqual(self.actor.balance, before_actor)
        self.assertEqual(self.owner.balance, before_owner)
        self.assertEqual(self.goal.saved_amount, 0)

    def test_sibling_cannot_request_goal_completion(self):
        self.login_as(self.actor)
        response = self.client.post(
            reverse("child_request_goal_completion", args=[self.goal.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, GoalStatus.ACTIVE)

    def test_sibling_cannot_resubmit_task_claim(self):
        self.login_as(self.actor)
        response = self.client.post(
            reverse("child_resubmit_task", args=[self.claim.pk]),
            {},
        )
        self.assertEqual(response.status_code, 404)
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, RequestStatus.NEEDS_CHANGES)

    def test_sibling_cannot_open_task_evidence(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                self.claim.evidence_image = SimpleUploadedFile(
                    "full.webp",
                    b"full-bytes",
                    content_type="image/webp",
                )
                self.claim.evidence_thumbnail = SimpleUploadedFile(
                    "thumb.webp",
                    b"thumb-bytes",
                    content_type="image/webp",
                )
                self.claim.save(
                    update_fields=["evidence_image", "evidence_thumbnail"]
                )
                self.login_as(self.actor)
                for size in ("thumbnail", "full"):
                    with self.subTest(size=size):
                        response = self.client.get(
                            reverse("task_evidence", args=[self.claim.pk, size])
                        )
                        self.assertEqual(response.status_code, 404)

    def test_point_gift_debits_only_the_logged_in_sender(self):
        self.login_as(self.actor)
        response = self.client.post(
            reverse("child_give_points"),
            {"recipient": self.owner.pk, "amount": 7},
        )
        self.assertRedirects(response, reverse("child_dashboard"))
        self.actor.refresh_from_db()
        self.owner.refresh_from_db()
        self.assertEqual(self.actor.balance, 43)
        self.assertEqual(self.owner.balance, 87)

    def test_point_gift_cannot_use_sibling_as_implicit_sender(self):
        """Even with a funded sibling, the session child remains the only debit source."""
        post_ledger_entry(
            child=self.owner,
            delta=20,
            kind=LedgerKind.ADJUSTMENT,
            description="Extra owner funds",
            actor=self.parent,
        )
        self.owner.refresh_from_db()
        owner_before = self.owner.balance
        self.actor.balance = 0
        self.actor.save(update_fields=["balance"])
        self.login_as(self.actor)
        response = self.client.post(
            reverse("child_give_points"),
            {"recipient": self.owner.pk, "amount": 5},
        )
        self.assertRedirects(response, reverse("child_dashboard"))
        self.actor.refresh_from_db()
        self.owner.refresh_from_db()
        self.assertEqual(self.actor.balance, 0)
        self.assertEqual(self.owner.balance, owner_before)
