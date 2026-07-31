from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from economy.models import (
    ChildProfile,
    DevicePairingLink,
    DeviceToken,
    PushSubscription,
)


@override_settings(DEVICE_PAIRING_REQUIRED=True, SESSION_COOKIE_SECURE=True)
class DevicePairingTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user(
            "parent",
            password="Safe-pairing-password-123!",
            is_staff=True,
        )
        self.child = ChildProfile(name="Private Child", theme_selected=True)
        self.child.set_pin("1234")
        self.child.save()

    def test_unpaired_device_does_not_reveal_child_profile(self):
        response = self.client.get(reverse("child_select"))

        self.assertContains(response, "This device is not set up yet")
        self.assertNotContains(response, self.child.name)
        self.assertNotContains(response, 'name="pin"', html=False)

    def test_parent_can_pair_current_device_and_child_session_is_bound_to_it(self):
        self.client.force_login(self.parent)

        response = self.client.post(
            reverse("parent_pair_device"),
            {"label": "Kitchen tablet"},
        )

        self.assertRedirects(response, reverse("child_select"))
        cookie = response.cookies["kk_device"]
        self.assertTrue(cookie["secure"])
        self.assertTrue(cookie["httponly"])
        device = DeviceToken.objects.get()
        self.assertEqual(device.label, "Kitchen tablet")
        self.assertNotEqual(device.token_hash, cookie.value)

        response = self.client.post(
            reverse("child_select"),
            {"child_id": self.child.pk, "pin": "1234"},
        )
        self.assertRedirects(response, reverse("child_dashboard"))
        self.assertEqual(self.client.session["child_device_id"], device.pk)

    def test_pairing_actions_share_a_two_column_row(self):
        self.client.force_login(self.parent)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, 'class="device-pairing-actions"', html=False)
        self.assertContains(response, "Allow children on this device")
        self.assertContains(response, "Create private pairing link")

    def test_pairing_link_is_single_use_and_expires(self):
        link, raw_token = DevicePairingLink.issue(created_by=self.parent)

        first = self.client.post(
            reverse("pair_device_via_link"),
            {"token": raw_token},
        )
        self.assertRedirects(first, reverse("child_select"))
        link.refresh_from_db()
        self.assertIsNotNone(link.used_at)

        second = self.client.post(
            reverse("pair_device_via_link"),
            {"token": raw_token},
        )
        self.assertRedirects(second, reverse("pair_device_via_link"))

        expired, expired_token = DevicePairingLink.issue(created_by=self.parent)
        expired.expires_at = timezone.now() - timedelta(seconds=1)
        expired.save(update_fields=["expires_at"])
        response = self.client.post(
            reverse("pair_device_via_link"),
            {"token": expired_token},
        )
        self.assertRedirects(response, reverse("pair_device_via_link"))

    def test_pairing_link_supports_secure_safari_csrf_post(self):
        _link, raw_token = DevicePairingLink.issue(created_by=self.parent)
        csrf_client = Client(enforce_csrf_checks=True)
        pairing_url = reverse("pair_device_via_link")

        page = csrf_client.get(pairing_url, secure=True)

        self.assertEqual(page["Cache-Control"], "no-store")
        self.assertEqual(page["Referrer-Policy"], "same-origin")
        csrf_token = page.cookies["csrftoken"].value

        response = csrf_client.post(
            pairing_url,
            {
                "token": raw_token,
                "csrfmiddlewaretoken": csrf_token,
            },
            secure=True,
            HTTP_REFERER=f"https://testserver{pairing_url}",
        )

        self.assertRedirects(response, reverse("child_select"))
        self.assertIn("kk_device", response.cookies)

    def test_revoking_device_removes_its_push_subscriptions(self):
        device, _raw_token = DeviceToken.issue(
            created_by=self.parent,
            label="Phone",
        )
        PushSubscription.objects.create(
            child=self.child,
            device=device,
            endpoint="https://push.example/device",
            p256dh="key",
            auth="auth",
        )
        self.client.force_login(self.parent)

        response = self.client.post(
            reverse("parent_revoke_device", args=[device.pk]),
        )

        self.assertRedirects(
            response,
            f"{reverse('parent_dashboard')}#parent-settings",
        )
        device.refresh_from_db()
        self.assertIsNotNone(device.revoked_at)
        self.assertFalse(PushSubscription.objects.exists())

    def test_revoked_cookie_invalidates_existing_child_session(self):
        device, raw_token = DeviceToken.issue(
            created_by=self.parent,
            label="Old phone",
        )
        self.client.cookies["kk_device"] = raw_token
        response = self.client.post(
            reverse("child_select"),
            {"child_id": self.child.pk, "pin": "1234"},
        )
        self.assertRedirects(response, reverse("child_dashboard"))

        device.revoked_at = timezone.now()
        device.save(update_fields=["revoked_at"])
        response = self.client.get(reverse("child_dashboard"))

        self.assertRedirects(response, reverse("child_select"))
        self.assertNotIn("child_id", self.client.session)
