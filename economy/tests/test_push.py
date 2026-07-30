import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils.translation import override

from economy.models import ChildProfile, PushSubscription, Reward, RewardRequest, Task, TaskClaim
from economy.push import _currency_amount, notify_reward_decision, notify_task_decision


@override_settings(
    VAPID_PRIVATE_KEY="test-private-key",
    VAPID_SUBJECT="mailto:test@example.com",
)
class ChildDecisionPushTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user("parent")
        self.child = ChildProfile.objects.create(name="Gabija", theme_selected=True)
        self.other_child = ChildProfile.objects.create(name="Augustas", theme_selected=True)
        PushSubscription.objects.create(
            child=self.child,
            endpoint="https://push.example/gabija",
            p256dh="gabija-key",
            auth="gabija-auth",
        )
        PushSubscription.objects.create(
            child=self.other_child,
            endpoint="https://push.example/augustas",
            p256dh="augustas-key",
            auth="augustas-auth",
        )
        PushSubscription.objects.create(
            user=self.parent,
            endpoint="https://push.example/parent",
            p256dh="parent-key",
            auth="parent-auth",
        )

    @patch("economy.push.webpush")
    def test_task_decision_targets_only_the_affected_child(self, webpush):
        task = Task.objects.create(title="Paklota lova", reward=20)
        claim = TaskClaim.objects.create(
            child=self.child,
            task=task,
            task_title=task.title,
            reward_snapshot=task.reward,
        )

        with override("lt"):
            notify_task_decision(claim, approved=True)

        webpush.assert_called_once()
        self.assertEqual(
            webpush.call_args.kwargs["subscription_info"]["endpoint"],
            "https://push.example/gabija",
        )
        payload = json.loads(webpush.call_args.kwargs["data"])
        self.assertEqual(payload["title"], "Tavo darbas patvirtintas")
        self.assertEqual(payload["body"], "Paklota lova: +20 taškų")
        self.assertEqual(payload["url"], "/vaikas/mano/#darbai")

    def test_lithuanian_notification_currency_uses_correct_forms(self):
        with override("lt"):
            for value, expected in (
                (1, "1 taškas"),
                (2, "2 taškai"),
                (9, "9 taškai"),
                (10, "10 taškų"),
                (21, "21 taškas"),
            ):
                with self.subTest(value=value):
                    self.assertEqual(_currency_amount(value, self.child), expected)

            self.child.theme = "block_world"
            self.assertEqual(_currency_amount(2, self.child), "2 smaragdai")
            self.child.theme = "magic_academy"
            self.assertEqual(_currency_amount(1, self.child), "1 galeonas")

    @patch("economy.push.webpush")
    def test_reward_rejection_includes_reason_and_targets_only_child(self, webpush):
        reward = Reward.objects.create(title="Filmas", cost=50)
        request = RewardRequest.objects.create(
            child=self.child,
            reward=reward,
            reward_title=reward.title,
            cost_snapshot=reward.cost,
            rejection_reason="Pirmiausia atlik darbus.",
        )

        with override("lt"):
            notify_reward_decision(request, approved=False)

        webpush.assert_called_once()
        payload = json.loads(webpush.call_args.kwargs["data"])
        self.assertEqual(payload["title"], "Tavo prizo prašymas atmestas")
        self.assertIn("Pirmiausia atlik darbus.", payload["body"])
        self.assertEqual(payload["url"], "/vaikas/mano/#prizai")
