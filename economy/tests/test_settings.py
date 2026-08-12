import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from economy.email_config import smtp_config
from economy.forms import ChildEditForm
from economy.models import ChildProfile, FamilySettings, PenaltyTemplate, Reward, Task

ROOT = Path(__file__).resolve().parents[2]


class FamilySettingsSingletonTests(TestCase):
    def test_update_fields_save_recovers_when_singleton_row_is_missing(self):
        FamilySettings.objects.filter(pk=1).delete()
        ghost = FamilySettings(pk=1, family_name="Ghost", currency_name="Old")
        ghost._state.adding = False
        ghost._state.db = "default"
        ghost.family_name = "Aurora"
        ghost.currency_name = "Tokenai"

        ghost.save(update_fields=["family_name", "currency_name"])

        family = FamilySettings.objects.get(pk=1)
        self.assertEqual(family.family_name, "Aurora")
        self.assertEqual(family.currency_name, "Tokenai")


class DefaultSettingsTests(SimpleTestCase):
    def test_debug_defaults_to_false_without_environment_override(self):
        environment = os.environ.copy()
        environment.pop("KINKUDOS_DEBUG", None)
        environment["KINKUDOS_SECRET_KEY"] = "test-only-secret"

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from kinkudos import settings; print(settings.DEBUG)",
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "False")


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
                "lottery_enabled": "on",
                "lottery_ticket_cost": 25,
                "lottery_weekly_limit": 4,
                "evidence_retention_days": 30,
                "feedback_screenshot_retention_days": 90,
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('parent_dashboard')}#parent-settings",
        )
        family = FamilySettings.load()
        self.assertEqual(family.family_name, "Aurora")
        self.assertTrue(family.lottery_enabled)
        self.assertEqual(family.lottery_ticket_cost, 25)
        self.assertEqual(family.lottery_weekly_limit, 4)

    def test_family_settings_use_clear_labels_and_group_dividers(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, "Points for a task photo")
        self.assertContains(response, "Surprise card price")
        self.assertContains(response, "Weekly card limit")
        self.assertContains(response, "Keep feedback images for")
        self.assertContains(response, 'class="catalog-divider"', count=3)

    def test_network_access_panel_explains_open_and_restricted_states(self):
        self.client.force_login(self.admin)

        open_response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(open_response, "IP restrictions disabled")
        self.assertContains(open_response, "service-status-bad")
        self.assertContains(open_response, "No IP addresses are blocked.")
        self.assertContains(open_response, 'data-open-dialog="network-access-dialog"')

        family = FamilySettings.load()
        family.network_access_mode = FamilySettings.NetworkAccessMode.CHILDREN
        family.allowed_networks = "192.0.2.0/24"
        family.save(update_fields=["network_access_mode", "allowed_networks"])

        restricted_response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(restricted_response, "Child access restricted")
        self.assertContains(restricted_response, "service-status-good")
        self.assertContains(
            restricted_response,
            "Parent access is not restricted by IP.",
        )
        self.assertContains(restricted_response, "192.0.2.0/24")

    def test_catalog_titles_use_the_shared_system_typography_class(self):
        Task.objects.create(title="Clean the kitchen", reward=10, icon="🧹")
        self.client.force_login(self.admin)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(
            response,
            '<span class="catalog-title">Clean the kitchen',
            html=False,
        )

    def test_catalog_changes_return_to_the_catalogs_panel(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("parent_create_catalog", args=["task"]),
            {"title": "Kitchen", "reward": 10, "icon": "🧹"},
        )
        self.assertRedirects(
            response,
            f"{reverse('parent_dashboard')}#parent-catalogs",
            fetch_redirect_response=False,
        )

    def test_family_lottery_switch_can_be_disabled(self):
        self.client.force_login(self.admin)

        self.client.post(
            reverse("parent_update_family_preferences"),
            {
                "family_name": "",
                "photo_bonus_points": 0,
                "birthday_points": 0,
                "lottery_ticket_cost": 15,
                "lottery_weekly_limit": 3,
                "evidence_retention_days": 30,
                "feedback_screenshot_retention_days": 90,
            },
        )

        self.assertFalse(FamilySettings.load().lottery_enabled)

    def test_lottery_price_and_weekly_limit_must_be_positive(self):
        self.client.force_login(self.admin)

        self.client.post(
            reverse("parent_update_family_preferences"),
            {
                "family_name": "",
                "photo_bonus_points": 0,
                "birthday_points": 0,
                "lottery_enabled": "on",
                "lottery_ticket_cost": 0,
                "lottery_weekly_limit": 0,
                "evidence_retention_days": 30,
                "feedback_screenshot_retention_days": 90,
            },
        )

        family = FamilySettings.load()
        self.assertEqual(family.lottery_ticket_cost, 15)
        self.assertEqual(family.lottery_weekly_limit, 3)

    @patch("economy.views.parent_settings.verify_smtp")
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

    @patch("economy.views.parent_settings.verify_smtp")
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

    @patch("economy.views.parent_settings.verify_smtp")
    def test_non_admin_cannot_change_smtp(self, verify):
        self.client.force_login(self.parent)
        self.client.post(reverse("parent_configure_smtp"), self.smtp_payload())
        verify.assert_not_called()

    def test_catalog_edit_labels_omit_trailing_colons(self):
        Task.objects.create(title="Tidy", reward=3)
        PenaltyTemplate.objects.create(title="Late", amount=-2)
        Reward.objects.create(title="Movie", cost=5)
        self.client.force_login(self.admin)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, "<label>Task<input", count=1, html=False)
        self.assertContains(response, "<label>Penalty<input", count=1, html=False)
        self.assertContains(response, "<label>Reward<input", count=1, html=False)
        self.assertContains(response, "<label>Icon<input", count=3, html=False)
        self.assertNotContains(response, "Task:<input", html=False)
        self.assertNotContains(response, "Penalty:<input", html=False)
        self.assertNotContains(response, "Reward:<input", html=False)
        self.assertNotContains(response, "Icon:<input", html=False)

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

        content = response.content.decode()
        email_panel = content.split('<article class="panel email-panel">', 1)[1].split(
            "</article>",
            1,
        )[0]

        self.assertIn('class="service-details"', email_panel)
        self.assertIn(">Edit settings</button>", email_panel)
        self.assertNotIn("Edit email settings", email_panel)
        self.assertNotIn('class="backup-status-grid"', email_panel)

    def test_family_preferences_use_compact_rows_and_wrapped_help_text(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, 'class="settings-row"', count=7, html=False)
        self.assertContains(response, 'class="settings-row checkbox-field"', count=1)
        self.assertContains(response, "Weekly card limit")
        self.assertContains(
            response,
            "The limit resets every Monday for each child. The default is 3.",
        )
        self.assertContains(
            response,
            '<small class="helptext">Shown in family-facing headings and messages.</small>',
            html=False,
        )

    def test_checkbox_labels_are_inline_and_child_copy_is_short(self):
        child = ChildProfile.objects.create(name="Checkbox child")
        self.assertEqual(
            ChildEditForm(child=child).fields["lottery_enabled"].label,
            "Enable surprise cards",
        )

        stylesheet = (Path(__file__).resolve().parents[2] / "static" / "css" / "app.css").read_text(
            encoding="utf-8",
        )
        self.assertIn(
            '.stack-form p:has(> input[type="checkbox"]) { display: flex; flex-wrap: wrap; align-items: center;',
            stylesheet,
        )
        self.assertIn(
            '.stack-form p:has(> input[type="checkbox"]) > .helptext { flex: 0 0 100%;',
            stylesheet,
        )
        self.assertIn("margin-left: 0;", stylesheet)

    def test_settings_actions_and_account_panels_use_shared_spacing(self):
        stylesheet = (Path(__file__).resolve().parents[2] / "static" / "css" / "app.css").read_text(
            encoding="utf-8",
        )
        self.assertIn(
            ".network-access-panel > .button, .email-panel > .button { display: flex; margin-top: 18px;",
            stylesheet,
        )
        self.assertIn(
            ".backup-actions { justify-content: flex-end; margin-top: 18px; }",
            stylesheet,
        )
        self.assertIn(
            ".account-management { display: grid; gap: 18px; }",
            stylesheet,
        )

    def test_existing_accounts_use_one_list_and_dialog_editing(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("parent_dashboard"))
        script = (Path(__file__).resolve().parents[2] / "static" / "js" / "app.js").read_text(
            encoding="utf-8",
        )

        self.assertContains(response, '<h3>Existing accounts</h3>', html=False)
        self.assertContains(response, 'data-account-create-type', html=False)
        self.assertContains(response, 'class="account-list-heading">Parent accounts', html=False)
        self.assertContains(response, 'class="account-list-heading">Child profiles', html=False)
        self.assertContains(response, 'data-open-dialog="edit-parent-account-', html=False)
        self.assertContains(response, 'class="action-dialog account-edit-dialog"', html=False)
        self.assertNotContains(response, 'data-toggle-edit="parent-account-', html=False)
        self.assertIn('document.querySelector("[data-account-create-type]")', script)
        self.assertIn('dialog[data-reset-on-close]', script)

    def test_settings_are_grouped_without_a_redundant_category_heading(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("parent_dashboard"))
        content = response.content.decode()
        settings = content[content.index('id="parent-settings"') : content.index('id="parent-history"')]

        self.assertNotContains(response, "Children and access")
        self.assertIn('id="settings-everyday-heading"', settings)
        self.assertIn("Everyday", settings)
        self.assertIn("People and devices", settings)
        self.assertIn(">Server<", settings)
        self.assertIn("Saves family preferences only.", settings)
        self.assertLess(
            settings.index("existing-accounts-panel"),
            settings.index("account-create-panel"),
        )
        for heading in (
            "Family",
            "Points and tasks",
            "Surprise cards",
            "Data and retention",
            "Child devices",
            "Network and security",
            "Email and notifications",
            "Backups",
            "Accounts",
            "Family feedback",
        ):
            self.assertIn(
                f'class="settings-summary-label">{heading}</span>',
                settings,
            )
        self.assertEqual(settings.count("settings-summary-status"), 3)
        self.assertNotContains(response, ">Rewards and goals<", html=False)

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
