from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from economy.models import (
    AssignedTask,
    AssignedTaskBatch,
    ChildProfile,
    DeviceToken,
    FamilySettings,
    GoalMode,
    LotteryTicket,
    RequestStatus,
    Reward,
    RewardRequest,
    SavingsGoal,
    Task,
    TaskClaim,
)


@override_settings(DEVICE_PAIRING_REQUIRED=True, SESSION_COOKIE_SECURE=True)
class ChildPairingRequiredMatrixTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user(
            "pairing-matrix-parent",
            password="Safe-pairing-matrix-123!",
            is_staff=True,
        )
        self.child = ChildProfile(name="Matrix Child", theme_selected=True)
        self.child.set_pin("1234")
        self.child.save()
        self.device, self.raw_token = DeviceToken.issue(
            created_by=self.parent,
            label="Matrix tablet",
        )
        self.other_device, self.other_raw_token = DeviceToken.issue(
            created_by=self.parent,
            label="Other tablet",
        )
        self.task = Task.objects.create(title="Matrix task", reward=10)
        self.claim = TaskClaim.objects.create(
            child=self.child,
            task=self.task,
            task_title=self.task.title,
            reward_snapshot=self.task.reward,
            status=RequestStatus.NEEDS_CHANGES,
        )
        self.reward = Reward.objects.create(title="Matrix reward", cost=5)
        self.reward_request = RewardRequest.objects.create(
            child=self.child,
            reward=self.reward,
            reward_title=self.reward.title,
            cost_snapshot=self.reward.cost,
        )
        self.batch = AssignedTaskBatch.objects.create(
            child=self.child,
            assigned_by=self.parent,
        )
        self.assigned = AssignedTask.objects.create(
            batch=self.batch,
            title_snapshot="Assigned",
            reward_snapshot=5,
        )
        self.ticket = LotteryTicket.objects.create(
            child=self.child,
            week_start=timezone.localdate(),
            values=[1, 2, 3, 1, 4, 5, 1, 6, 7],
            prize_amount=1,
        )
        self.goal = SavingsGoal.objects.create(
            child=self.child,
            title="Matrix goal",
            target_amount=20,
            mode=GoalMode.SAVED,
        )
        family = FamilySettings.load()
        family.lottery_enabled = True
        family.save(update_fields=["lottery_enabled"])

    def forge_unpaired_child_session(self):
        self.client.cookies.pop(settings.DEVICE_COOKIE_NAME, None)
        session = self.client.session
        session["child_id"] = self.child.pk
        session["child_device_id"] = self.device.pk
        session.save()

    def forge_mismatched_device_session(self):
        self.client.cookies[settings.DEVICE_COOKIE_NAME] = self.other_raw_token
        session = self.client.session
        session["child_id"] = self.child.pk
        session["child_device_id"] = self.device.pk
        session.save()

    def pair_and_login(self):
        self.client.cookies[settings.DEVICE_COOKIE_NAME] = self.raw_token
        response = self.client.post(
            reverse("child_select"),
            {"child_id": self.child.pk, "pin": "1234"},
        )
        self.assertRedirects(response, reverse("child_dashboard"))

    def _blocked_cases(self):
        return (
            ("get", "child_dashboard", (), {}),
            ("get", "child_state", (), {}),
            ("post", "child_submit_task", (self.task.pk,), {}),
            ("post", "child_complete_assigned_task", (self.assigned.pk,), {}),
            ("post", "child_resubmit_task", (self.claim.pk,), {}),
            ("post", "child_acknowledge_task_response", (self.claim.pk,), {}),
            ("post", "child_request_reward", (self.reward.pk,), {}),
            ("post", "child_cancel_reward", (self.reward_request.pk,), {}),
            ("post", "child_purchase_lottery_ticket", (), {}),
            ("post", "child_reveal_lottery_ticket", (self.ticket.pk,), {}),
            ("post", "child_create_proposal", (), {"title": "X", "proposal_type": "reward"}),
            ("post", "child_set_goal_mode", (self.goal.pk,), {"mode": GoalMode.AVAILABLE}),
            ("post", "child_add_goal_points", (self.goal.pk,), {"amount": 1}),
            ("post", "child_request_goal_completion", (self.goal.pk,), {}),
            ("post", "child_set_theme", (), {"theme": "neutral"}),
            ("post", "child_give_points", (), {"recipient": self.child.pk, "amount": 1}),
            ("post", "child_set_birth_date", (), {"birth_date": "2015-01-01"}),
            ("post", "child_change_pin", (), {
                "current_pin": "1234",
                "new_pin": "4321",
                "confirm_pin": "4321",
            }),
        )

    def _assert_matrix_blocked(self, forge):
        select_url = reverse("child_select")
        for method, name, args, data in self._blocked_cases():
            with self.subTest(method=method, name=name):
                forge()
                url = reverse(name, args=args)
                if method == "get":
                    response = self.client.get(url)
                else:
                    response = self.client.post(url, data)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, select_url)
                self.assertIsNone(self.client.session.get("child_id"))

    def test_forged_child_session_without_device_is_blocked(self):
        self._assert_matrix_blocked(self.forge_unpaired_child_session)

    def test_mismatched_device_binding_is_blocked(self):
        self._assert_matrix_blocked(self.forge_mismatched_device_session)

    def test_task_evidence_without_pairing_is_private(self):
        self.forge_unpaired_child_session()
        response = self.client.get(
            reverse("task_evidence", args=[self.claim.pk, "full"])
        )
        self.assertEqual(response.status_code, 404)
        self.assertIsNone(self.client.session.get("child_id"))

    def test_child_push_subscribe_without_pairing_redirects(self):
        self.forge_unpaired_child_session()
        response = self.client.post(
            reverse("child_push_subscribe"),
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("child_select"))

    def test_paired_child_can_open_dashboard_and_state(self):
        self.pair_and_login()
        dashboard = self.client.get(reverse("child_dashboard"))
        self.assertEqual(dashboard.status_code, 200)
        state = self.client.get(reverse("child_state"))
        self.assertEqual(state.status_code, 200)
        self.assertIn("signature", state.json())
