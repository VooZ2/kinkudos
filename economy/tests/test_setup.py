from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from economy.models import FamilySettings


@override_settings(SETUP_TOKEN="setup-test-token")
class BrowserSetupTests(TestCase):
    def payload(self, **overrides):
        data = {
            "setup_token": "setup-test-token",
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

    def test_setup_email_checkbox_is_kept_inline_with_its_label(self):
        response = self.client.get(reverse("setup"))
        self.assertContains(response, 'id="id_configure_smtp"')
        stylesheet = (Path(settings.BASE_DIR) / "static" / "css" / "app.css").read_text(
            encoding="utf-8"
        )
        selector = ".setup-card .stack-form p:has(> #id_configure_smtp)"
        self.assertIn(f"{selector} {{ display: flex; align-items: center;", stylesheet)
        self.assertIn(f"{selector} > #id_configure_smtp {{ order: -1;", stylesheet)

    def test_setup_creates_the_first_admin_and_family(self):
        response = self.client.post(reverse("setup"), self.payload())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Setup complete")
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
