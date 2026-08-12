import base64
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from economy.models import ChildProfile, PushSubscription


class PushSubscriptionModelTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user("parent")
        self.child = ChildProfile.objects.create(name="Child")
        self.resolve_patcher = patch(
            "economy.models.require_global_destination",
            return_value=[],
        )
        self.resolve_patcher.start()
        self.addCleanup(self.resolve_patcher.stop)

    @staticmethod
    def keys():
        return (
            base64.urlsafe_b64encode(b"\x04" + b"p" * 64).rstrip(b"=").decode(),
            base64.urlsafe_b64encode(b"a" * 16).rstrip(b"=").decode(),
        )

    def test_model_validation_rejects_non_public_push_endpoint(self):
        p256dh, auth = self.keys()
        subscription = PushSubscription(
            user=self.parent,
            endpoint="https://10.0.0.1/push",
            p256dh=p256dh,
            auth=auth,
        )

        with self.assertRaises(ValidationError):
            subscription.full_clean()

    def test_model_validation_accepts_a_browser_shaped_subscription(self):
        p256dh, auth = self.keys()
        subscription = PushSubscription(
            user=self.parent,
            endpoint="https://push.example.test/subscription",
            p256dh=p256dh,
            auth=auth,
        )

        subscription.full_clean()

    def test_model_validation_accepts_a_public_ipv6_push_endpoint(self):
        p256dh, auth = self.keys()
        subscription = PushSubscription(
            user=self.parent,
            endpoint="https://[2606:4700:4700::1111]/subscription",
            p256dh=p256dh,
            auth=auth,
        )

        subscription.full_clean()
