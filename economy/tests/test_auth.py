from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from economy.models import PushSubscription
from economy.services import deactivate_parent_account


@override_settings(LANGUAGE_CODE="en")
class ParentAccountPermissionTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            "admin",
            email="admin@example.test",
            password="Safe-admin-password-123!",
            is_staff=True,
        )
        self.parent = get_user_model().objects.create_user(
            "parent",
            email="parent@example.test",
            password="Safe-parent-password-123!",
        )

    @staticmethod
    def edit_payload(**overrides):
        payload = {
            "username": "changed",
            "email": "changed@example.test",
            "new_password": "Changed-admin-password-456!",
            "confirm_password": "Changed-admin-password-456!",
        }
        payload.update(overrides)
        return payload

    def test_non_staff_parent_cannot_change_an_administrator_account(self):
        self.client.force_login(self.parent)

        response = self.client.post(
            reverse("parent_edit_parent_account", args=[self.admin.pk]),
            self.edit_payload(),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.username, "admin")
        self.assertEqual(self.admin.email, "admin@example.test")
        self.assertTrue(self.admin.check_password("Safe-admin-password-123!"))
        self.assertContains(response, "Only a parent administrator can manage an administrator account.")

    def test_non_staff_parent_cannot_deactivate_an_administrator_or_its_push_subscription(self):
        subscription = PushSubscription.objects.create(
            user=self.admin,
            endpoint="https://push.example/admin",
            p256dh="admin-key",
            auth="admin-auth",
        )
        self.client.force_login(self.parent)

        response = self.client.post(
            reverse("parent_remove_parent_account", args=[self.admin.pk]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertTrue(PushSubscription.objects.filter(pk=subscription.pk).exists())

    def test_deactivating_a_parent_removes_its_push_subscriptions(self):
        subscription = PushSubscription.objects.create(
            user=self.parent,
            endpoint="https://push.example/parent",
            p256dh="parent-key",
            auth="parent-auth",
        )
        self.client.force_login(self.admin)

        self.client.post(reverse("parent_remove_parent_account", args=[self.parent.pk]))

        self.parent.refresh_from_db()
        self.assertFalse(self.parent.is_active)
        self.assertFalse(PushSubscription.objects.filter(pk=subscription.pk).exists())

    def test_last_active_administrator_cannot_be_removed_from_its_own_session(self):
        self.parent.delete()
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("parent_remove_parent_account", args=[self.admin.pk]),
            follow=True,
        )

        self.assertContains(response, "You cannot remove the account you are currently using.")
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_deactivation_guard_keeps_the_last_active_administrator(self):
        self.assertEqual(deactivate_parent_account(self.admin), 0)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_deactivation_guard_keeps_the_last_active_parent(self):
        self.admin.delete()

        self.assertEqual(deactivate_parent_account(self.parent), 0)
        self.parent.refresh_from_db()
        self.assertTrue(self.parent.is_active)
