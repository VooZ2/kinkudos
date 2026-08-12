from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from economy.models import BackupAuditEvent


@override_settings(LANGUAGE_CODE="en")
class BackupSettingsTests(TestCase):
    def setUp(self):
        self.password = "Safe-backup-admin-123!"
        self.admin = get_user_model().objects.create_user(
            "backup-admin",
            password=self.password,
            is_staff=True,
        )
        self.parent = get_user_model().objects.create_user(
            "backup-viewer",
            password="Safe-backup-viewer-123!",
        )

    def _status_response(self):
        return self.client.get(reverse("parent_backup_status"))

    @patch("economy.views.parent_settings.backup_status")
    def test_all_parents_can_see_status_but_only_admin_sees_controls(self, status):
        status.return_value = {
            "available": True,
            "configured": True,
            "provider": "backblaze_s3",
            "target": "s3:https://example.invalid/family/kinkudos",
            "is_fresh": True,
            "running": False,
            "last_success": None,
            "last_check": None,
            "error": "",
        }
        self.client.force_login(self.parent)
        payload = self._status_response().json()
        self.assertEqual(payload["summary_label"], "Enabled")
        self.assertTrue(payload["can_run"])

        dashboard = self.client.get(reverse("parent_dashboard"))
        self.assertContains(dashboard, "Backups")
        self.assertNotContains(dashboard, "Edit settings")
        self.assertNotContains(dashboard, "Back up now")

    @patch("economy.views.parent_settings.backup_status")
    def test_unconfigured_backup_uses_neutral_values_and_negative_status(self, status):
        status.return_value = {
            "available": True,
            "configured": False,
            "provider": "",
            "target": "",
            "is_fresh": False,
            "running": False,
            "last_success": None,
            "last_check": None,
            "error": "",
        }
        self.client.force_login(self.admin)

        payload = self._status_response().json()
        self.assertEqual(payload["summary_label"], "Not enabled")
        self.assertEqual(payload["summary_class"], "service-status-bad")
        self.assertEqual(payload["last_success_display"], "—")
        self.assertFalse(payload["can_run"])

        dashboard = self.client.get(reverse("parent_dashboard"))
        self.assertContains(dashboard, "Edit settings")
        self.assertContains(dashboard, "Your account password", count=3)
        self.assertNotContains(dashboard, "Your current parent password")
        self.assertNotContains(dashboard, "REPLACE_WITH_REPOSITORY")

    @patch("economy.views.parent_settings.backup_status")
    def test_unavailable_backup_warning_uses_separate_warning_block(self, status):
        status.return_value = {
            "available": False,
            "configured": False,
            "provider": "",
            "target": "",
            "is_fresh": False,
            "running": False,
            "last_success": None,
            "last_check": None,
            "error": "",
        }
        self.client.force_login(self.parent)

        payload = self._status_response().json()
        self.assertIn(
            "The backup service is unavailable. Ask the server administrator to check the backup container.",
            payload["unavailable_message"],
        )
        self.assertEqual(payload["summary_label"], "Attention needed")

    @patch("economy.views.parent_settings.backup_status")
    def test_admin_can_open_backup_settings_when_service_is_unavailable(self, status):
        status.return_value = {
            "available": False,
            "configured": False,
            "provider": "",
            "target": "",
            "is_fresh": False,
            "running": False,
            "last_success": None,
            "last_check": None,
            "error": "",
        }
        self.client.force_login(self.admin)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, ">Edit settings</button>")
        self.assertContains(response, 'data-open-dialog="backup-settings-dialog"', html=False)

    @patch("economy.views.parent_settings.backup_status")
    def test_configured_backup_without_success_uses_attention_status(self, status):
        status.return_value = {
            "available": True,
            "configured": True,
            "provider": "s3",
            "target": "s3.example.invalid/test/kinkudos",
            "is_fresh": False,
            "running": False,
            "last_success": None,
            "last_check": None,
            "error": "",
        }
        self.client.force_login(self.admin)

        payload = self._status_response().json()
        self.assertEqual(payload["summary_label"], "Attention needed")
        self.assertEqual(payload["last_success_display"], "Backups not completed")
        self.assertTrue(payload["can_run"])

    @patch("economy.views.parent_settings.backup_status")
    def test_running_backup_uses_the_main_status_indicator(self, status):
        status.return_value = {
            "available": True,
            "configured": True,
            "provider": "s3",
            "target": "s3.example.invalid/test/kinkudos",
            "is_fresh": True,
            "running": True,
            "last_success": None,
            "last_check": None,
            "error": "",
        }
        self.client.force_login(self.admin)

        payload = self._status_response().json()
        self.assertEqual(payload["summary_label"], "Copying")
        self.assertEqual(payload["summary_class"], "service-status-warning")
        self.assertTrue(payload["running"])

    def test_only_five_latest_backup_actions_are_shown(self):
        for index in range(7):
            BackupAuditEvent.objects.create(
                actor=self.admin,
                action=BackupAuditEvent.Action.CONFIGURED,
                target=f"backup-target-{index}",
            )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertEqual(len(response.context["backup_audit_events"]), 5)

    def test_parent_dashboard_does_not_query_backup_agent_on_html_render(self):
        self.client.force_login(self.admin)
        with patch("economy.views.parent_settings.backup_status") as settings_status:
            settings_status.return_value = {
                "available": True,
                "configured": True,
                "provider": "s3",
                "target": "s3.example.invalid/test/kinkudos",
                "is_fresh": True,
                "running": False,
                "last_success": None,
                "last_check": None,
                "error": "",
            }
            response = self.client.get(reverse("parent_dashboard"))
            self.assertEqual(response.status_code, 200)
            settings_status.assert_not_called()
            self.assertContains(response, "data-backup-status-url")
            self.assertContains(response, "Checking…")

    @patch("economy.views.parent_settings.configure_backup")
    def test_admin_can_verify_and_save_configuration(self, configure):
        configure.return_value = {
            "provider": "backblaze_s3",
            "target": "s3:https://s3.example.invalid/family/kinkudos",
        }
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("parent_configure_backup"),
            {
                "provider": "backblaze_s3",
                "endpoint": "s3.example.invalid",
                "bucket": "family",
                "region": "eu-test-1",
                "access_key_id": "key-id",
                "secret_access_key": "secret-key",
                "current_password": self.password,
            },
        )
        self.assertRedirects(response, f"{reverse('parent_dashboard')}#parent-settings")
        event = BackupAuditEvent.objects.get()
        self.assertEqual(event.actor, self.admin)
        self.assertEqual(event.action, BackupAuditEvent.Action.CONFIGURED)
        configure.assert_called_once()

    @patch("economy.views.parent_settings.configure_backup")
    def test_wrong_password_does_not_send_credentials_to_agent(self, configure):
        self.client.force_login(self.admin)
        self.client.post(
            reverse("parent_configure_backup"),
            {
                "provider": "backblaze_s3",
                "endpoint": "s3.example.invalid",
                "bucket": "family",
                "access_key_id": "key-id",
                "secret_access_key": "secret-key",
                "current_password": "wrong-password",
            },
        )
        configure.assert_not_called()
        self.assertFalse(BackupAuditEvent.objects.exists())

    @patch("economy.views.parent_settings.request_manual_backup")
    @patch("economy.views.parent_settings.backup_status")
    def test_admin_can_request_manual_backup(self, status, request_backup):
        status.return_value = {
            "provider": "backblaze_s3",
            "target": "s3:https://s3.example.invalid/family/kinkudos",
        }
        self.client.force_login(self.admin)
        response = self.client.post(reverse("parent_run_backup"))
        self.assertRedirects(response, f"{reverse('parent_dashboard')}#parent-settings")
        request_backup.assert_called_once_with()
        self.assertEqual(
            BackupAuditEvent.objects.get().action,
            BackupAuditEvent.Action.MANUAL_RUN,
        )

    @patch("economy.views.parent_settings.request_manual_backup")
    def test_non_admin_cannot_request_manual_backup(self, request_backup):
        self.client.force_login(self.parent)
        self.client.post(reverse("parent_run_backup"))
        request_backup.assert_not_called()
