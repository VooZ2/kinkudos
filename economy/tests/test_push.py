import base64
import json
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import override
from py_vapid import Vapid

from economy.models import (
    AssignedTask,
    AssignedTaskBatch,
    BirthDateChangeRequest,
    ChildProfile,
    DeviceToken,
    PointGift,
    Proposal,
    ProposalType,
    PushSubscription,
    Reward,
    RewardRequest,
    Task,
    TaskClaim,
    Theme,
)
from economy.push import (
    _currency_amount,
    notify_assigned_tasks,
    notify_birth_date_change,
    notify_birth_date_decision,
    notify_gift_received,
    notify_proposal,
    notify_proposal_decision,
    notify_reward_decision,
    notify_reward_request,
    notify_task_decision,
)


class VapidFilePathTests(TestCase):
    def test_docker_secret_pem_path_is_accepted_by_vapid_library(self):
        key = ec.generate_private_key(ec.SECP256R1())
        pem = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "vapid_private.pem"
            path.write_bytes(pem)

            vapid = Vapid.from_file(str(path))
            headers = vapid.sign(
                {
                    "sub": "mailto:test@example.com",
                    "aud": "https://push.example",
                }
            )

        self.assertIn("Authorization", headers)


@override_settings(
    VAPID_PRIVATE_KEY="test-private-key",
    VAPID_SUBJECT="mailto:test@example.com",
)
class ChildDecisionPushTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user("parent")
        self.child = ChildProfile.objects.create(name="Child One", theme_selected=True)
        self.other_child = ChildProfile.objects.create(name="Child Two", theme_selected=True)
        self.child_device, _ = DeviceToken.issue(created_by=self.parent, label="One")
        self.other_device, _ = DeviceToken.issue(created_by=self.parent, label="Two")
        PushSubscription.objects.create(
            child=self.child,
            device=self.child_device,
            endpoint="https://push.example/child_one",
            p256dh="child_one-key",
            auth="child_one-auth",
        )
        PushSubscription.objects.create(
            child=self.other_child,
            device=self.other_device,
            endpoint="https://push.example/child_two",
            p256dh="child_two-key",
            auth="child_two-auth",
        )
        PushSubscription.objects.create(
            user=self.parent,
            endpoint="https://push.example/parent",
            p256dh="parent-key",
            auth="parent-auth",
        )

    @patch("economy.push.webpush")
    def test_assigned_task_notification_uses_child_theme(self, webpush):
        self.child.theme = Theme.MAGIC_ACADEMY
        self.child.save(update_fields=["theme"])
        batch = AssignedTaskBatch.objects.create(
            child=self.child,
            assigned_by=self.parent,
        )
        AssignedTask.objects.create(
            batch=batch,
            title_snapshot="Pakloti lovą",
            reward_snapshot=10,
        )

        with override("lt"):
            notify_assigned_tasks(batch)

        webpush.assert_called_once()
        payload = json.loads(webpush.call_args.kwargs["data"])
        self.assertEqual(payload["title"], "Šiandienos užburti darbai")
        self.assertIn("vidurnaktį", payload["body"])
        self.assertEqual(
            payload["url"],
            f"{reverse('child_dashboard')}#paskirti-darbai",
        )
        self.assertEqual(webpush.call_args.kwargs["timeout"], 10)

    @patch("economy.push.webpush")
    def test_webpush_calls_use_an_explicit_timeout(self, webpush):
        task = Task.objects.create(title="Paklota lova", reward=20)
        claim = TaskClaim.objects.create(
            child=self.child,
            task=task,
            task_title=task.title,
            reward_snapshot=task.reward,
        )

        notify_task_decision(claim, approved=True)

        webpush.assert_called_once()
        self.assertEqual(webpush.call_args.kwargs["timeout"], 10)

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
            "https://push.example/child_one",
        )
        payload = json.loads(webpush.call_args.kwargs["data"])
        self.assertEqual(payload["title"], "Tavo darbas patvirtintas")
        self.assertEqual(payload["body"], "Paklota lova: +20 taškų")
        self.assertEqual(payload["url"], f"{reverse('child_dashboard')}#darbai")

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
    def test_gift_notification_uses_recipient_theme_without_amount(self, webpush):
        self.child.theme = Theme.ART_STUDIO
        self.child.save(update_fields=["theme"])
        gift = PointGift.objects.create(
            sender=self.other_child,
            recipient=self.child,
            amount=7,
        )

        with override("lt"):
            notify_gift_received(gift)

        webpush.assert_called_once()
        payload = json.loads(webpush.call_args.kwargs["data"])
        self.assertEqual(payload["title"], "Gavai dovanų!")
        self.assertEqual(payload["body"], "Child Two tau padovanojo perlų.")

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
        self.assertEqual(payload["url"], f"{reverse('child_dashboard')}#prizai")

    @patch("economy.push.webpush")
    def test_parent_approval_requests_target_parent_subscriptions(self, webpush):
        reward = Reward.objects.create(title="Film", cost=50)
        reward_request = RewardRequest.objects.create(
            child=self.child,
            reward=reward,
            reward_title=reward.title,
            cost_snapshot=reward.cost,
        )
        proposal = Proposal.objects.create(
            child=self.child,
            proposal_type=ProposalType.REWARD,
            title="New reward",
            suggested_cost=60,
        )
        change = BirthDateChangeRequest.objects.create(
            child=self.child,
            requested_birth_date=date(2018, 7, 30),
        )

        for notifier, item, expected_title in (
            (notify_reward_request, reward_request, "A reward is awaiting approval"),
            (notify_proposal, proposal, "A new suggestion is awaiting approval"),
            (notify_birth_date_change, change, "A birthday change is awaiting approval"),
        ):
            with self.subTest(notifier=notifier.__name__):
                webpush.reset_mock()
                notifier(item)
                webpush.assert_called_once()
                self.assertEqual(
                    webpush.call_args.kwargs["subscription_info"]["endpoint"],
                    "https://push.example/parent",
                )
                payload = json.loads(webpush.call_args.kwargs["data"])
                self.assertEqual(payload["title"], expected_title)
                self.assertEqual(payload["url"], reverse("parent_dashboard"))

    @patch("economy.push.webpush")
    def test_proposal_and_birthday_decisions_target_affected_child(self, webpush):
        proposal = Proposal.objects.create(
            child=self.child,
            proposal_type=ProposalType.GOAL,
            title="Bike",
            suggested_cost=500,
        )
        change = BirthDateChangeRequest.objects.create(
            child=self.child,
            requested_birth_date=date(2018, 7, 30),
        )

        for notifier, item, expected_title in (
            (lambda value: notify_proposal_decision(value, approved=True), proposal, "Your suggestion was approved"),
            (lambda value: notify_birth_date_decision(value, approved=False), change, "Your birthday change was rejected"),
        ):
            with self.subTest(expected_title=expected_title):
                webpush.reset_mock()
                notifier(item)
                webpush.assert_called_once()
                self.assertEqual(
                    webpush.call_args.kwargs["subscription_info"]["endpoint"],
                    "https://push.example/child_one",
                )
                self.assertEqual(
                    json.loads(webpush.call_args.kwargs["data"])["title"], expected_title,
                )


class PushSubscriptionValidationTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user(
            "push-parent",
            password="Safe-push-parent-123!",
        )
        self.child = ChildProfile.objects.create(
            name="Push child",
            theme_selected=True,
        )
        self.resolve_patcher = patch(
            "economy.models.require_global_destination",
            return_value=[],
        )
        self.resolve_patcher.start()
        self.addCleanup(self.resolve_patcher.stop)

    @staticmethod
    def keys():
        return {
            "p256dh": base64.urlsafe_b64encode(b"\x04" + b"p" * 64)
            .rstrip(b"=")
            .decode(),
            "auth": base64.urlsafe_b64encode(b"a" * 16).rstrip(b"=").decode(),
        }

    def payload(self, endpoint="https://push.example.test/subscription"):
        return json.dumps({"endpoint": endpoint, "keys": self.keys()})

    def subscribe_parent(self, endpoint="https://push.example.test/subscription"):
        self.client.force_login(self.parent)
        return self.client.post(
            reverse("push_subscribe"),
            data=self.payload(endpoint),
            content_type="application/json",
        )

    def test_valid_https_endpoint_and_keys_are_saved(self):
        response = self.subscribe_parent()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            PushSubscription.objects.filter(
                user=self.parent,
                endpoint="https://push.example.test/subscription",
            ).exists()
        )

    def test_http_local_and_private_endpoints_are_rejected(self):
        for endpoint in (
            "http://push.example.test/subscription",
            "https://localhost/subscription",
            "https://127.0.0.1/subscription",
            "https://192.168.1.20/subscription",
        ):
            with self.subTest(endpoint=endpoint):
                response = self.subscribe_parent(endpoint)
                self.assertEqual(response.status_code, 400)

    def test_oversized_endpoint_and_malformed_keys_are_rejected(self):
        oversized = self.subscribe_parent(
            "https://push.example.test/" + "x" * 2048,
        )
        self.assertEqual(oversized.status_code, 400)

        self.client.force_login(self.parent)
        malformed = self.client.post(
            reverse("push_subscribe"),
            data=json.dumps(
                {
                    "endpoint": "https://push.example.test/malformed",
                    "keys": {"p256dh": "not-a-key", "auth": "also-not-a-key"},
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(malformed.status_code, 400)

    def test_parent_subscription_limit_is_enforced(self):
        for number in range(10):
            response = self.subscribe_parent(f"https://push.example.test/{number}")
            self.assertEqual(response.status_code, 200)

        response = self.subscribe_parent("https://push.example.test/too-many")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(PushSubscription.objects.filter(user=self.parent).count(), 10)

    @override_settings(DEVICE_PAIRING_REQUIRED=False)
    def test_child_subscription_uses_the_same_validation(self):
        session = self.client.session
        session["child_id"] = self.child.pk
        session.save()

        response = self.client.post(
            reverse("child_push_subscribe"),
            data=self.payload("https://push.example.test/child"),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(PushSubscription.objects.filter(child=self.child).exists())


class InactiveParentPushTests(TestCase):
    @patch("economy.push.webpush")
    def test_inactive_parent_subscriptions_are_not_notified(self, webpush):
        parent = get_user_model().objects.create_user("inactive-parent")
        parent.is_active = False
        parent.save(update_fields=["is_active"])
        child = ChildProfile.objects.create(name="Child", theme_selected=True)
        reward = Reward.objects.create(title="Reward", cost=10)
        request = RewardRequest.objects.create(
            child=child,
            reward=reward,
            reward_title=reward.title,
            cost_snapshot=reward.cost,
        )
        PushSubscription.objects.create(
            user=parent,
            endpoint="https://push.example.test/inactive",
            p256dh="key",
            auth="auth",
        )

        notify_reward_request(request)

        webpush.assert_not_called()
