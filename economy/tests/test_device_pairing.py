import tempfile
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
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

    def test_unpaired_device_cannot_download_child_avatar(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                self.child.avatar = SimpleUploadedFile(
                    "private.webp",
                    b"private-avatar",
                    content_type="image/webp",
                )
                self.child.save(update_fields=["avatar"])

                response = self.client.get(
                    reverse("child_avatar", args=[self.child.pk])
                )

                self.assertEqual(response.status_code, 404)

    def test_paired_device_can_download_child_avatar(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                self.child.avatar = SimpleUploadedFile(
                    "private.webp",
                    b"private-avatar",
                    content_type="image/webp",
                )
                self.child.save(update_fields=["avatar"])
                _device, raw_token = DeviceToken.issue(
                    created_by=self.parent,
                    label="Paired tablet",
                )
                self.client.cookies[settings.DEVICE_COOKIE_NAME] = raw_token

                response = self.client.get(
                    reverse("child_avatar", args=[self.child.pk])
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(b"".join(response.streaming_content), b"private-avatar")

    def test_parent_can_pair_current_device_and_child_session_is_bound_to_it(self):
        self.client.force_login(self.parent)

        response = self.client.post(
            reverse("parent_pair_device"),
            {"label": "Kitchen tablet"},
            HTTP_USER_AGENT=(
                "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                "Mobile/15E148 Safari/604.1"
            ),
        )

        self.assertRedirects(response, reverse("child_select"))
        cookie = response.cookies["kk_device"]
        self.assertTrue(cookie["secure"])
        self.assertTrue(cookie["httponly"])
        device = DeviceToken.objects.get()
        self.assertEqual(device.label, "Kitchen tablet")
        self.assertEqual(device.device_kind, DeviceToken.Kind.TABLET)
        self.assertEqual(device.device_platform, "ios")
        self.assertEqual(device.device_browser, "safari")
        self.assertRegex(device.device_code, r"^[A-Z2-9]{6}$")
        self.assertNotEqual(device.token_hash, cookie.value)

        response = self.client.post(
            reverse("child_select"),
            {"child_id": self.child.pk, "pin": "1234"},
        )
        self.assertRedirects(response, reverse("child_dashboard"))
        self.assertEqual(self.client.session["child_device_id"], device.pk)

    def test_active_device_cookie_is_renewed_when_the_device_is_used(self):
        _device, raw_token = DeviceToken.issue(
            created_by=self.parent,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
        )
        self.client.cookies[settings.DEVICE_COOKIE_NAME] = raw_token

        response = self.client.get(reverse("child_select"))

        refreshed_cookie = response.cookies[settings.DEVICE_COOKIE_NAME]
        self.assertEqual(
            refreshed_cookie["max-age"],
            settings.DEVICE_COOKIE_MAX_AGE,
        )
        self.assertTrue(refreshed_cookie["secure"])
        self.assertTrue(refreshed_cookie["httponly"])

    def test_pairing_actions_share_a_two_column_row(self):
        self.client.force_login(self.parent)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, 'class="device-pairing-actions"', html=False)
        self.assertContains(response, "Allow on this device")
        self.assertContains(response, "Send a link")

    def test_parent_dashboard_identifies_devices_without_avatar_initials(self):
        device, _raw_token = DeviceToken.issue(
            created_by=self.parent,
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                "Mobile/15E148 Safari/604.1"
            ),
        )
        self.client.force_login(self.parent)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, 'href="#icon-mobile-screen-button"', html=False)
        self.assertContains(response, "iPhone · Safari")
        self.assertContains(response, device.device_code)
        self.assertContains(response, "device-revoke-button", html=False)
        self.assertContains(response, 'class="device-revoke-icon"', html=False)

    def test_generate_pairing_link_opens_share_dialog_on_settings(self):
        self.client.force_login(self.parent)

        response = self.client.post(reverse("parent_generate_pairing_link"), follow=True)

        self.assertTrue(response.redirect_chain)
        self.assertTrue(
            response.redirect_chain[-1][0].startswith(reverse("parent_dashboard"))
        )
        self.assertContains(response, 'id="device-pairing-share-dialog"', html=False)
        self.assertContains(response, "Private pairing link")
        self.assertContains(response, reverse("pair_device_via_link"), html=False)
        self.assertContains(response, "Share…")
        self.assertContains(response, ">Copy<", html=False)
        self.assertContains(response, 'href="#icon-share-nodes"', html=False)
        self.assertNotContains(response, "is ready to share")
        self.assertNotContains(response, 'data-share-device-pairing hidden')
        self.assertContains(response, "dialog.showModal")
        html = response.content.decode()
        dialog_html = html[
            html.index('id="device-pairing-share-dialog"') : html.index(
                "id=\"push-help-dialog\""
            )
        ]
        self.assertIn(">Copy<", dialog_html)
        self.assertNotIn("#icon-clipboard-check", dialog_html)
        self.assertNotIn("Copy link", dialog_html)
        self.assertLess(
            dialog_html.index("share-dialog-toolbar"),
            dialog_html.index("danger-warning"),
        )
        self.assertLess(
            dialog_html.index("danger-warning"),
            dialog_html.index("dialog-actions"),
        )
        self.assertTrue(DevicePairingLink.objects.exists())

    def test_inactive_devices_are_hidden_from_settings_list(self):
        active, _ = DeviceToken.issue(created_by=self.parent, label="Active tablet")
        inactive, _ = DeviceToken.issue(created_by=self.parent, label="Stale phone")
        DeviceToken.objects.filter(pk=inactive.pk).update(
            created_at=timezone.now() - timedelta(days=45),
            last_used_at=timezone.now() - timedelta(days=45),
        )
        self.client.force_login(self.parent)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, "Active tablet")
        self.assertNotContains(response, "Stale phone")
        self.assertContains(response, "Revoke all child devices")
        inactive.refresh_from_db()
        self.assertTrue(inactive.is_inactive)
        self.assertFalse(active.is_inactive)

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

        for directive in ("no-store", "no-cache", "must-revalidate", "private"):
            self.assertIn(directive, page["Cache-Control"])
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
