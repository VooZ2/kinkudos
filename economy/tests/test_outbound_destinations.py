import ipaddress
import socket
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, override_settings

from economy.email_config import verify_smtp
from economy.net import require_global_destination


def _addrinfo(ip, port=443):
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    return [(family, socket.SOCK_STREAM, 0, "", (ip, port))]


class OutboundDestinationPolicyTests(SimpleTestCase):
    @patch(
        "economy.net.socket.getaddrinfo",
        return_value=_addrinfo("8.8.8.8"),
    )
    def test_public_destination_is_accepted(self, _getaddrinfo):
        addresses = require_global_destination("smtp.example.test", 587)
        self.assertEqual(addresses, [ipaddress.ip_address("8.8.8.8")])

    @patch(
        "economy.net.socket.getaddrinfo",
        return_value=_addrinfo("10.0.0.5"),
    )
    def test_private_destination_is_rejected(self, _getaddrinfo):
        with self.assertRaises(ValueError):
            require_global_destination("smtp.internal.test", 587)

    @override_settings(SMTP_ALLOW_PRIVATE_DESTINATIONS=True)
    @patch(
        "economy.net.socket.getaddrinfo",
        return_value=_addrinfo("10.0.0.5"),
    )
    @patch("economy.email_config.smtplib.SMTP")
    def test_smtp_private_escape_hatch_allows_lan_host(self, smtp_class, _getaddrinfo):
        client = smtp_class.return_value.__enter__.return_value
        verify_smtp(
            {
                "host": "smtp.lan.test",
                "port": 587,
                "security": "tls",
                "username": "user",
                "password": "pass",
            }
        )
        smtp_class.assert_called_once()
        client.starttls.assert_called_once()
        client.login.assert_called_once_with("user", "pass")

    @override_settings(SMTP_ALLOW_PRIVATE_DESTINATIONS=False)
    @patch(
        "economy.net.socket.getaddrinfo",
        return_value=_addrinfo("169.254.169.254"),
    )
    def test_smtp_verify_blocks_link_local_metadata_targets(self, _getaddrinfo):
        with self.assertRaises(ValueError):
            verify_smtp(
                {
                    "host": "metadata.example.test",
                    "port": 587,
                    "security": "tls",
                    "username": "user",
                    "password": "pass",
                }
            )


class PushDestinationResolutionTests(SimpleTestCase):
    @patch(
        "economy.models.require_global_destination",
        side_effect=ValueError("private"),
    )
    def test_push_hostname_resolving_to_private_is_rejected(self, _require):
        import base64

        from economy.models import validate_push_subscription_data

        p256dh = base64.urlsafe_b64encode(b"\x04" + b"p" * 64).rstrip(b"=").decode()
        auth = base64.urlsafe_b64encode(b"a" * 16).rstrip(b"=").decode()
        with self.assertRaises(ValidationError):
            validate_push_subscription_data(
                "https://evil.example.test/push",
                p256dh,
                auth,
            )
