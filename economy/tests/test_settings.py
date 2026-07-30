from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from economy.email_config import smtp_config
from economy.models import FamilySettings, PenaltyTemplate, Reward, Task


@override_settings(LANGUAGE_CODE="en")
class ParentSettingsTests(TestCase):
    def setUp(self):
        self.password = "Safe-settings-admin-123!"
        self.admin = get_user_model().objects.create_user(
            "settings-admin",
            password=self.password,
            is_staff=True,
        )
        self.parent = get_user_model().objects.create_user(
            "settings-parent",
            password="Safe-settings-parent-123!",
        )

    def test_family_name_can_be_changed_with_family_preferences(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("parent_update_family_preferences"),
            {
                "family_name": "Aurora",
                "photo_bonus_points": 2,
                "birthday_points": 10,
                "evidence_retention_days": 30,
                "feedback_screenshot_retention_days": 90,
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('parent_dashboard')}#parent-settings",
        )
        self.assertEqual(FamilySettings.load().family_name, "Aurora")

    def test_family_settings_use_clear_labels_and_group_dividers(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, "Points for a task photo")
        self.assertContains(response, "Keep feedback images for")
        self.assertContains(response, 'class="catalog-divider"', count=5)

    @patch("economy.views.verify_smtp")
    def test_admin_password_is_required_before_saving_smtp(self, verify):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            with override_settings(SMTP_CONFIG_PATH=path):
                self.client.force_login(self.admin)
                self.client.post(
                    reverse("parent_configure_smtp"),
                    self.smtp_payload(current_password="wrong-password"),
                )

                verify.assert_not_called()
                self.assertFalse(path.exists())

    @patch("economy.views.verify_smtp")
    def test_admin_can_verify_and_save_smtp_outside_database(self, verify):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            with override_settings(SMTP_CONFIG_PATH=path):
                self.client.force_login(self.admin)
                response = self.client.post(
                    reverse("parent_configure_smtp"),
                    self.smtp_payload(),
                )

                self.assertRedirects(
                    response,
                    f"{reverse('parent_dashboard')}#parent-settings",
                )
                verify.assert_called_once()
                self.assertEqual(smtp_config()["host"], "smtp.example.test")
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                self.assertNotContains(
                    self.client.get(reverse("parent_dashboard")),
                    "smtp-secret",
                )

    @patch("economy.views.verify_smtp")
    def test_non_admin_cannot_change_smtp(self, verify):
        self.client.force_login(self.parent)
        self.client.post(reverse("parent_configure_smtp"), self.smtp_payload())
        verify.assert_not_called()

    def test_catalog_edit_labels_have_colons(self):
        Task.objects.create(title="Tidy", reward=3)
        PenaltyTemplate.objects.create(title="Late", amount=-2)
        Reward.objects.create(title="Movie", cost=5)
        self.client.force_login(self.admin)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, "Task:<input", count=1)
        self.assertContains(response, "Penalty:<input", count=1)
        self.assertContains(response, "Reward:<input", count=1)
        self.assertContains(response, "Icon:<input", count=3)

    def test_email_status_uses_compact_details_and_short_edit_label(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(
                (
                    '{"enabled": true, "host": "smtp.example.test", "port": 587, '
                    '"from_email": "sender@example.test", '
                    '"feedback_email": "family@example.test"}'
                ),
                encoding="utf-8",
            )
            with override_settings(SMTP_CONFIG_PATH=path):
                self.client.force_login(self.admin)
                response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, 'class="service-details"', count=1)
        self.assertContains(response, ">Edit settings</button>", count=1)
        self.assertNotContains(response, "Edit email settings")
        self.assertNotContains(response, 'class="backup-status-grid"')

    def test_family_preferences_use_compact_rows_and_wrapped_help_text(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, 'class="settings-row"', count=5, html=False)
        self.assertContains(
            response,
            '<small class="helptext">Shown in family-facing headings and messages.</small>',
            html=False,
        )

    def smtp_payload(self, **overrides):
        payload = {
            "enabled": "on",
            "host": "smtp.example.test",
            "port": 587,
            "security": "tls",
            "username": "mailer",
            "password": "smtp-secret",
            "from_email": "sender@example.test",
            "feedback_email": "family@example.test",
            "current_password": self.password,
        }
        payload.update(overrides)
        return payload
