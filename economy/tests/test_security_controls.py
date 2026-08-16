import re
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from economy.forms import NetworkAccessForm
from economy.middleware import TrustedProxyMiddleware
from economy.models import AttemptCounter, ChildProfile, FamilySettings, FeedbackReport
from economy.net import client_ip
from economy.rate_limit import register_attempt


class AttemptCounterTests(TestCase):
    def test_fixed_window_limit_and_reset(self):
        now = timezone.now()
        scope = AttemptCounter.Scope.PARENT_LOGIN_IP

        self.assertTrue(
            register_attempt(scope, "192.0.2.1", window_seconds=60, limit=2, now=now)
        )
        self.assertTrue(
            register_attempt(scope, "192.0.2.1", window_seconds=60, limit=2, now=now)
        )
        self.assertFalse(
            register_attempt(scope, "192.0.2.1", window_seconds=60, limit=2, now=now)
        )
        self.assertTrue(
            register_attempt(
                scope,
                "192.0.2.1",
                window_seconds=60,
                limit=2,
                now=now + timedelta(minutes=2),
            )
        )
        counter = AttemptCounter.objects.first()
        self.assertNotIn("192.0.2.1", counter.key_hash)


class ClientIpTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_default_trusted_proxies_are_loopback_only(self):
        from pathlib import Path

        settings_source = Path(settings.BASE_DIR, "kinkudos", "settings.py").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            '"KINKUDOS_TRUSTED_PROXIES",\n    "127.0.0.0/8,::1/128",',
            settings_source,
        )
        self.assertNotIn(
            '"127.0.0.0/8,::1/128,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"',
            settings_source,
        )

    @override_settings(TRUSTED_PROXY_NETWORKS=["127.0.0.0/8", "::1/128"])
    def test_private_lan_peer_does_not_receive_forwarded_client_ip(self):
        request = self.factory.get(
            "/",
            REMOTE_ADDR="10.0.0.5",
            HTTP_X_FORWARDED_FOR="198.51.100.9",
        )
        self.assertEqual(client_ip(request), "10.0.0.5")

    @override_settings(TRUSTED_PROXY_NETWORKS=["10.0.0.0/8"])
    def test_forwarded_chain_is_used_only_for_trusted_peer(self):
        trusted = self.factory.get(
            "/",
            REMOTE_ADDR="10.0.0.5",
            HTTP_X_FORWARDED_FOR="198.51.100.9, 10.0.0.4",
        )
        untrusted = self.factory.get(
            "/",
            REMOTE_ADDR="203.0.113.8",
            HTTP_X_FORWARDED_FOR="198.51.100.9",
        )

        self.assertEqual(client_ip(trusted), "198.51.100.9")
        self.assertEqual(client_ip(untrusted), "203.0.113.8")

    @override_settings(TRUSTED_PROXY_NETWORKS=["10.0.0.0/8"])
    def test_invalid_forwarded_chain_falls_back_to_peer(self):
        request = self.factory.get(
            "/",
            REMOTE_ADDR="10.0.0.5",
            HTTP_X_FORWARDED_FOR="not-an-ip",
        )
        self.assertEqual(client_ip(request), "10.0.0.5")

    @override_settings(TRUSTED_PROXY_NETWORKS=["10.0.0.0/8"])
    def test_untrusted_peer_cannot_spoof_forwarded_security_headers(self):
        request = self.factory.get(
            "/",
            REMOTE_ADDR="203.0.113.8",
            HTTP_X_FORWARDED_FOR="198.51.100.9",
            HTTP_X_FORWARDED_PROTO="https",
        )
        response = TrustedProxyMiddleware(
            lambda received: HttpResponse(
                f"{received.META.get('HTTP_X_FORWARDED_FOR', '')}|"
                f"{received.META.get('HTTP_X_FORWARDED_PROTO', '')}"
            )
        )(request)

        self.assertEqual(response.content, b"|")


@override_settings(DEVICE_PAIRING_REQUIRED=False, LANGUAGE_CODE="en")
class ChildPinSiteRateLimitTests(TestCase):
    def setUp(self):
        self.child = ChildProfile(name="Pin child", theme_selected=True)
        self.child.set_pin("1234")
        self.child.save()
        self.other = ChildProfile(name="Other pin child", theme_selected=True)
        self.other.set_pin("1234")
        self.other.save()

    def post_pin(self, child=None, pin="0000"):
        child = child or self.child
        return self.client.post(
            reverse("child_select"),
            {"child_id": child.pk, "pin": pin},
        )

    def clear_profile_lock(self, child):
        ChildProfile.objects.filter(pk=child.pk).update(
            failed_pin_attempts=0,
            locked_until=None,
        )

    @patch("economy.views.session.logger.warning")
    def test_site_wide_pin_threshold_is_alarm_only(self, warning):
        # Seed past the site threshold without burning device/profile/IP budgets.
        for _ in range(61):
            register_attempt(
                AttemptCounter.Scope.CHILD_PIN_SITE,
                "site",
                window_seconds=300,
                limit=60,
            )
        response = self.post_pin()
        self.assertContains(response, "Incorrect PIN.")
        self.assertNotContains(response, "Too many PIN attempts")
        warning.assert_called()
        self.clear_profile_lock(self.child)
        response = self.post_pin(pin="1234")
        self.assertRedirects(response, reverse("child_dashboard"))

    def test_device_pin_limit_still_blocks_login(self):
        # Profile AttemptCounter limit is 10; rotate so device (15) binds first.
        window_start = timezone.now().replace(second=0, microsecond=0)
        with patch("django.utils.timezone.now", return_value=window_start):
            for index in range(15):
                child = self.child if index < 10 else self.other
                response = self.post_pin(child=child)
                self.assertContains(response, "Incorrect PIN.")
                self.clear_profile_lock(child)
            response = self.post_pin(pin="1234")
        self.assertContains(response, "Too many PIN attempts. Try again later.")
        self.assertNotIn("child_id", self.client.session)


class ContentSecurityPolicyTests(TestCase):
    def setUp(self):
        self.parent = get_user_model().objects.create_user(
            "csp-parent",
            password="Safe-csp-parent-password-123!",
        )

    def test_responses_use_nonce_protected_inline_scripts(self):
        responses = [
            self.client.get(url)
            for url in (
                reverse("parent_login"),
                reverse("pair_device_via_link"),
            )
        ]
        self.client.force_login(self.parent)
        responses.append(
            self.client.post(reverse("parent_generate_pairing_link"), follow=True)
        )

        for response in responses:
            self.assertEqual(response.status_code, 200)
            policy = response["Content-Security-Policy"]
            match = re.search(r"script-src 'self' 'nonce-([^']+)'", policy)
            self.assertIsNotNone(match)
            nonce = match.group(1)
            script_tags = re.findall(
                r"<script(?:\s[^>]*)?>",
                response.content.decode(),
                flags=re.IGNORECASE,
            )
            inline_script_tags = [tag for tag in script_tags if " src=" not in tag]

            self.assertTrue(inline_script_tags)
            self.assertTrue(
                all(f'nonce="{nonce}"' in tag for tag in inline_script_tags)
            )
            self.assertNotIn("'unsafe-inline'", match.group(0))
            self.assertIn("object-src 'none'", policy)
            self.assertIn("frame-ancestors 'none'", policy)


@override_settings(DEVICE_PAIRING_REQUIRED=False)
class NetworkAccessTests(TestCase):
    def setUp(self):
        self.child = ChildProfile.objects.create(
            name="Network child",
            theme_selected=True,
        )

    def sign_in_child(self):
        session = self.client.session
        session["child_id"] = self.child.pk
        session.save()

    def restrict_children(self):
        family = FamilySettings.load()
        family.network_access_mode = FamilySettings.NetworkAccessMode.CHILDREN
        family.allowed_networks = "192.0.2.0/24"
        family.save(update_fields=["network_access_mode", "allowed_networks"])

    def test_child_area_can_be_restricted_without_blocking_parent_login(self):
        get_user_model().objects.create_user("parent", password="Safe-parent-pass-123!")
        self.restrict_children()

        child_response = self.client.get(
            reverse("child_select"),
            REMOTE_ADDR="198.51.100.2",
        )
        parent_response = self.client.get(
            reverse("parent_login"),
            REMOTE_ADDR="198.51.100.2",
        )

        self.assertEqual(child_response.status_code, 403)
        self.assertEqual(parent_response.status_code, 200)

    def test_active_child_session_does_not_block_parent_login(self):
        parent = get_user_model().objects.create_user(
            "parent",
            password="Safe-parent-pass-123!",
        )
        self.restrict_children()
        self.sign_in_child()

        response = self.client.post(
            reverse("parent_login"),
            {
                "username": parent.username,
                "password": "Safe-parent-pass-123!",
            },
            REMOTE_ADDR="198.51.100.2",
        )

        self.assertRedirects(
            response,
            reverse("parent_dashboard"),
            fetch_redirect_response=False,
        )
        self.assertNotIn("child_id", self.client.session)

    @patch("economy.views.session.smtp_config", return_value={"enabled": True})
    def test_active_child_session_does_not_block_parent_password_recovery(self, smtp_config):
        self.restrict_children()
        self.sign_in_child()

        response = self.client.get(
            reverse("password_reset"),
            REMOTE_ADDR="198.51.100.2",
        )

        self.assertEqual(response.status_code, 200)
        smtp_config.assert_called()

    def test_restricted_child_session_cannot_submit_feedback(self):
        self.restrict_children()
        self.sign_in_child()

        response = self.client.post(
            reverse("submit_feedback"),
            {
                "report_type": "bug",
                "description": "This must be blocked.",
            },
            REMOTE_ADDR="198.51.100.2",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(FeedbackReport.objects.exists())

    def test_restricted_child_session_cannot_open_its_feedback_screenshot(self):
        report = FeedbackReport.objects.create(
            description="Private screenshot",
            child=self.child,
            reporter_name=self.child.name,
            reporter_role="child",
            app_version="26.6.4",
        )
        self.restrict_children()
        self.sign_in_child()

        response = self.client.get(
            reverse("feedback_screenshot", args=[report.pk]),
            REMOTE_ADDR="198.51.100.2",
        )

        self.assertEqual(response.status_code, 403)

    def test_authenticated_parent_can_use_shared_feedback_route(self):
        parent = get_user_model().objects.create_user(
            "parent",
            password="Safe-parent-pass-123!",
        )
        self.restrict_children()
        self.client.force_login(parent)

        response = self.client.post(
            reverse("submit_feedback"),
            {
                "report_type": "idea",
                "description": "Parent feedback is allowed.",
            },
            REMOTE_ADDR="198.51.100.2",
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(FeedbackReport.objects.get().parent, parent)

    def test_open_mode_keeps_child_area_available(self):
        response = self.client.get(
            reverse("child_select"),
            REMOTE_ADDR="198.51.100.2",
        )

        self.assertEqual(response.status_code, 200)

    def test_all_mode_restricts_parent_and_child_routes(self):
        family = FamilySettings.load()
        family.network_access_mode = FamilySettings.NetworkAccessMode.ALL
        family.allowed_networks = "192.0.2.0/24"
        family.save(update_fields=["network_access_mode", "allowed_networks"])

        response = self.client.get(
            reverse("parent_login"),
            REMOTE_ADDR="198.51.100.2",
        )

        self.assertEqual(response.status_code, 403)

    def test_restrict_all_form_requires_current_ip_in_allowlist(self):
        form = NetworkAccessForm(
            {
                "network_access_mode": FamilySettings.NetworkAccessMode.ALL,
                "allowed_networks": "192.0.2.0/24",
                "current_password": "unused",
            },
            current_ip="198.51.100.2",
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Include your current IP address",
            str(form.errors["allowed_networks"]),
        )


@override_settings(DEVICE_PAIRING_REQUIRED=False)
class LoginRateLimitTests(TestCase):
    def setUp(self):
        self.password = "Safe-parent-password-123!"
        get_user_model().objects.create_user(
            "parent",
            password=self.password,
            is_staff=True,
        )

    def test_parent_account_limit_blocks_repeated_guesses(self):
        login_url = reverse("parent_login")
        for _attempt in range(10):
            response = self.client.post(
                login_url,
                {"username": "parent", "password": "wrong-password"},
                REMOTE_ADDR="192.0.2.10",
            )
            self.assertEqual(response.status_code, 200)

        blocked = self.client.post(
            login_url,
            {"username": "parent", "password": self.password},
            REMOTE_ADDR="192.0.2.10",
        )

        self.assertContains(blocked, "Too many sign-in attempts")
