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

    @patch("economy.views.backup_status")
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
        response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(response, "Backups")
        self.assertContains(response, "Enabled")
        self.assertNotContains(response, "Edit settings")
        self.assertNotContains(response, "Back up now")

    @patch("economy.views.backup_status")
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

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, "Not enabled")
        self.assertContains(response, "service-status-bad")
        self.assertNotContains(response, "REPLACE_WITH_REPOSITORY")
        self.assertNotContains(response, "Backups not completed")
        self.assertContains(response, "Edit settings")
        self.assertContains(response, "Your account password", count=2)
        self.assertNotContains(response, "Your current parent password")

    @patch("economy.views.backup_status")
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

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, "Attention needed")
        self.assertContains(response, "Backups not completed")
        self.assertContains(response, "danger-warning")

    @patch("economy.views.backup_status")
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

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, "Copying")
        self.assertContains(response, "service-status-warning")
        self.assertNotContains(response, "Backup in progress")

    @patch("economy.views.configure_backup")
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

    @patch("economy.views.configure_backup")
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

    @patch("economy.views.request_manual_backup")
    @patch("economy.views.backup_status")
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

    @patch("economy.views.request_manual_backup")
    def test_non_admin_cannot_request_manual_backup(self, request_backup):
        self.client.force_login(self.parent)
        self.client.post(reverse("parent_run_backup"))
        request_backup.assert_not_called()
