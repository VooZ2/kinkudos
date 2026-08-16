from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from economy.models import AttemptCounter, FamilySettings

SETUP_TOKEN = "setup-test-token-with-enough-entropy-32"


@override_settings(SETUP_TOKEN=SETUP_TOKEN)
class BrowserSetupTests(TestCase):
    def payload(self, **overrides):
        data = {
            "setup_token": SETUP_TOKEN,
            "username": "first-parent",
            "email": "parent@example.test",
            "password1": "Strong-first-parent-123!",
            "password2": "Strong-first-parent-123!",
            "family_name": "Aurora",
            "default_language": "lt",
            "timezone_name": "Europe/Vilnius",
        }
        data.update(overrides)
        return data

    def test_empty_installation_redirects_to_setup(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("setup"), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("health")).status_code, 200)

    def test_setup_uses_installation_neutral_copy_in_english_and_lithuanian(self):
        response = self.client.get(reverse("setup"))
        self.assertContains(response, "Set up the system")
        self.assertContains(
            response,
            "Enter the setup code configured for this installation.",
        )
        self.assertNotContains(response, "server installer")

        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "lt"
        response = self.client.get(reverse("setup"))
        self.assertContains(response, "Paruoškite sistemą")
        self.assertContains(
            response,
            "Įveskite šiam diegimui nustatytą paruošimo kodą.",
        )
        self.assertNotContains(response, "Paruoškite savo šeimą")

    def test_setup_email_checkbox_is_kept_after_its_inline_label(self):
        response = self.client.get(reverse("setup"))
        self.assertContains(response, 'id="id_configure_smtp"')
        self.assertContains(response, 'class="field-required"', count=16, html=False)
        stylesheet = (Path(settings.BASE_DIR) / "static" / "css" / "app.css").read_text(
            encoding="utf-8"
        )
        selector = '.setup-card .stack-form p:has(> input[type="checkbox"])'
        self.assertIn(f"{selector} {{ display: flex; align-items: center;", stylesheet)
        self.assertIn(
            f'{selector} > input[type="checkbox"] {{ order: 1;',
            stylesheet,
        )

    def test_setup_email_fields_are_enabled_only_when_requested(self):
        self.client.get(reverse("setup"))
        script = (Path(settings.BASE_DIR) / "static" / "js" / "app.js").read_text(
            encoding="utf-8"
        )
        self.assertIn('getElementById("id_configure_smtp")', script)
        self.assertIn("field.disabled = disabled;", script)
        self.assertIn("field.required = enabled;", script)
        self.assertIn('classList.toggle("field-required", enabled)', script)
        self.assertIn(
            'setupEmailToggle?.addEventListener("change", () => {',
            script,
        )
        self.assertIn("syncSetupEmailFields();", script)
        self.assertIn("decorateRequiredLabels();", script)

    def test_setup_uses_a_wide_two_column_desktop_layout(self):
        response = self.client.get(reverse("setup"))
        self.assertContains(response, 'class="narrow-card setup-card"', html=False)
        stylesheet = (Path(settings.BASE_DIR) / "static" / "css" / "app.css").read_text(
            encoding="utf-8"
        )
        self.assertIn(".auth-page .setup-card { width: min(860px, 100%); }", stylesheet)
        self.assertIn(
            ".setup-card .auth-help { max-width: 720px; margin: 28px 0 32px;",
            stylesheet,
        )
        self.assertIn(
            ".setup-card .stack-form { grid-template-columns: repeat(2, minmax(0, 1fr));",
            stylesheet,
        )
        self.assertIn("row-gap: 22px;", stylesheet)
        self.assertIn(
            ".setup-card .stack-form > p { min-width: 0; align-self: start; align-content: start; }",
            stylesheet,
        )
        self.assertIn(
            '.setup-card .stack-form > p > input:not([type="checkbox"]),',
            stylesheet,
        )
        self.assertIn(
            ".setup-card .stack-form { grid-template-columns: 1fr; }",
            stylesheet,
        )

    def test_setup_creates_the_first_admin_and_family(self):
        response = self.client.post(reverse("setup"), self.payload())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Setup complete")
        self.assertContains(response, 'data-copy-from="recovery-code-value"', html=False)
        self.assertContains(response, 'href="#icon-copy"', html=False)
        self.assertContains(response, 'aria-label="Copy"', html=False)
        self.assertContains(response, "setup-open-parent", html=False)
        parent = get_user_model().objects.get(username="first-parent")
        self.assertTrue(parent.is_staff)
        family = FamilySettings.load()
        self.assertEqual(family.family_name, "Aurora")
        self.assertEqual(family.default_language, "lt")
        self.assertEqual(family.timezone_name, "Europe/Vilnius")
        self.assertIsNotNone(family.setup_completed_at)
        self.assertTrue(family.recovery_code_hash)

    def test_incorrect_setup_code_creates_nothing(self):
        response = self.client.post(reverse("setup"), self.payload(setup_token="wrong"))
        self.assertContains(response, "The setup code is incorrect.")
        self.assertFalse(get_user_model().objects.exists())

    def test_existing_installation_never_exposes_setup(self):
        get_user_model().objects.create_user("existing", password="Safe-existing-pass-123!")
        response = self.client.get(reverse("setup"))
        self.assertRedirects(response, reverse("parent_login"), fetch_redirect_response=False)

    def test_setup_post_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse("setup"), self.payload())
        self.assertEqual(response.status_code, 403)

    @override_settings(USE_TZ=True)
    def test_setup_claim_is_rate_limited_by_ip(self):
        window_start = timezone.now().replace(second=0, microsecond=0)
        with mock.patch("django.utils.timezone.now", return_value=window_start):
            for _ in range(10):
                response = self.client.post(
                    reverse("setup"),
                    self.payload(setup_token="wrong-token-value"),
                )
                self.assertContains(response, "The setup code is incorrect.")
            response = self.client.post(reverse("setup"), self.payload())
        self.assertContains(response, "Too many setup attempts. Try again later.")
        self.assertFalse(get_user_model().objects.exists())
        self.assertTrue(
            AttemptCounter.objects.filter(
                scope=AttemptCounter.Scope.SETUP_CLAIM_IP
            ).exists()
        )

    @override_settings(SETUP_TOKEN="short-token")
    def test_weak_configured_setup_token_is_rejected(self):
        response = self.client.post(
            reverse("setup"),
            self.payload(setup_token="short-token"),
        )
        self.assertContains(response, "The configured setup code is too short.")
        self.assertFalse(get_user_model().objects.exists())
