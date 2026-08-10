import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from economy.forms import NetworkAccessForm
from economy.middleware import TrustedProxyMiddleware
from economy.models import AttemptCounter, FamilySettings
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
            self.client.post(reverse("parent_generate_pairing_link"))
        )

        for response in responses:
            self.assertEqual(response.status_code, 200)
            policy = response["Content-Security-Policy"]
            match = re.search(r"script-src 'self' 'nonce-([^']+)'", policy)
            self.assertIsNotNone(match)
            nonce = match.group(1)
            script_tags = re.findall(r"<script(?:\s[^>]*)?>", response.content.decode())
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
    def test_child_area_can_be_restricted_without_blocking_parent_login(self):
        get_user_model().objects.create_user("parent", password="Safe-parent-pass-123!")
        family = FamilySettings.load()
        family.network_access_mode = FamilySettings.NetworkAccessMode.CHILDREN
        family.allowed_networks = "192.0.2.0/24"
        family.save(update_fields=["network_access_mode", "allowed_networks"])

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
