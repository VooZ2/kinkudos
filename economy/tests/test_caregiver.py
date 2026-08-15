from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from economy.models import (
    CaregiverInvite,
    CaregiverProfile,
    ChildProfile,
    FamilySettings,
    RequestStatus,
    Task,
    TaskClaim,
)


@override_settings(LANGUAGE_CODE="en", DEVICE_PAIRING_REQUIRED=False)
class CaregiverGuestAccessTests(TestCase):
    def setUp(self):
        family = FamilySettings.load()
        family.setup_completed_at = timezone.now()
        family.family_name = "Jonaičiai"
        family.save(update_fields=["setup_completed_at", "family_name"])
        self.parent = get_user_model().objects.create_user(
            "parent",
            password="Safe-parent-password-123!",
        )
        self.child = ChildProfile.objects.create(name="Emilis")
        self.child.set_pin("1234")
        self.child.save()
        self.other_child = ChildProfile.objects.create(name="Urtė")
        self.other_child.set_pin("5678")
        self.other_child.save()
        self.client = Client()

    def test_settings_shows_guest_access_section(self):
        self.client.force_login(self.parent)
        response = self.client.get(reverse("parent_dashboard"))
        self.assertContains(response, "Guest access")
        self.assertContains(
            response,
            "Temporary access for grandparents, relatives, or babysitters",
        )

    def test_create_invite_opens_share_dialog_via_session(self):
        self.client.force_login(self.parent)
        response = self.client.post(
            reverse("parent_create_caregiver_invite"),
            {
                "label": "Senelė Ona",
                "access_until": (timezone.localdate() + timedelta(days=7)).isoformat(),
                "children": [self.child.pk],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Private sign-in link")
        self.assertContains(response, "caregiver-invite-share-dialog")
        self.assertContains(response, "Share…")
        self.assertContains(response, "Copy link")
        self.assertNotContains(response, "is ready to share")
        self.assertNotContains(response, 'data-share-caregiver-invite hidden')
        self.assertContains(response, "dialog.showModal")
        invite = CaregiverInvite.objects.get()
        self.assertTrue(invite.is_pending)
        self.assertEqual(invite.children.count(), 1)

    def test_invite_redeem_create_pin_and_login(self):
        invite, raw_token = CaregiverInvite.issue(
            created_by=self.parent,
            label="Senelė Ona",
            access_until=timezone.localdate() + timedelta(days=10),
            children=[self.child],
        )
        csrf = Client(enforce_csrf_checks=True)
        page = csrf.get(reverse("caregiver_invite_redeem"))
        token = page.cookies["csrftoken"].value
        redeem = csrf.post(
            reverse("caregiver_invite_redeem"),
            {"token": raw_token},
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(redeem.status_code, 302)
        self.assertEqual(redeem.url, reverse("caregiver_create_pin"))

        pin_page = csrf.get(reverse("caregiver_create_pin"))
        token = pin_page.cookies["csrftoken"].value
        created = csrf.post(
            reverse("caregiver_create_pin"),
            {"pin": "4321", "confirm_pin": "4321"},
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(created.status_code, 302)
        invite.refresh_from_db()
        self.assertIsNotNone(invite.used_at)
        caregiver = CaregiverProfile.objects.get()
        self.assertEqual(caregiver.label, "Senelė Ona")
        self.assertTrue(caregiver.children.filter(pk=self.child.pk).exists())
        self.assertEqual(
            created.url,
            reverse("caregiver_login", kwargs={"login_code": caregiver.login_code}),
        )

        login_page = csrf.get(
            reverse("caregiver_login", kwargs={"login_code": caregiver.login_code})
        )
        token = login_page.cookies["csrftoken"].value
        signed_in = csrf.post(
            reverse("caregiver_login", kwargs={"login_code": caregiver.login_code}),
            {"pin": "4321"},
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(signed_in.status_code, 302)
        self.assertEqual(signed_in.url, reverse("parent_dashboard"))
        dashboard = csrf.get(reverse("parent_dashboard"))
        self.assertContains(dashboard, "Guest area")
        self.assertNotContains(dashboard, 'data-parent-nav="settings"')
        self.assertContains(dashboard, "Emilis")
        self.assertNotContains(dashboard, "Urtė")

    def test_used_invite_redirects_to_login(self):
        invite, raw_token = CaregiverInvite.issue(
            created_by=self.parent,
            label="Senelė Ona",
            access_until=timezone.localdate() + timedelta(days=10),
            children=[self.child],
        )
        caregiver = CaregiverProfile.create_from_invite(invite=invite, raw_pin="1111")
        invite.used_at = timezone.now()
        invite.caregiver = caregiver
        invite.save(update_fields=["used_at", "caregiver"])
        response = self.client.post(
            reverse("caregiver_invite_redeem"),
            {"token": raw_token},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("caregiver_login", kwargs={"login_code": caregiver.login_code}),
        )

    def test_expired_invite_rejected(self):
        invite, raw_token = CaregiverInvite.issue(
            created_by=self.parent,
            label="Senelė Ona",
            access_until=timezone.localdate() + timedelta(days=10),
            children=[self.child],
        )
        invite.expires_at = timezone.now() - timedelta(minutes=1)
        invite.save(update_fields=["expires_at"])
        response = self.client.post(
            reverse("caregiver_invite_redeem"),
            {"token": raw_token},
            follow=True,
        )
        self.assertContains(response, "invalid or has expired")

    def test_caregiver_cannot_access_settings_or_other_child(self):
        invite, _raw = CaregiverInvite.issue(
            created_by=self.parent,
            label="Auklė",
            access_until=timezone.localdate() + timedelta(days=5),
            children=[self.child],
        )
        caregiver = CaregiverProfile.create_from_invite(invite=invite, raw_pin="9999")
        invite.used_at = timezone.now()
        invite.caregiver = caregiver
        invite.save(update_fields=["used_at", "caregiver"])
        self.client.force_login(caregiver.user)

        denied = self.client.post(reverse("parent_update_family_preferences"), {})
        self.assertEqual(denied.status_code, 302)
        self.assertEqual(denied.url, reverse("parent_dashboard"))

        unlock_other = self.client.post(
            reverse("parent_unlock_child", args=[self.other_child.pk])
        )
        self.assertEqual(unlock_other.status_code, 404)

    def test_caregiver_can_decide_task_for_assigned_child(self):
        invite, _raw = CaregiverInvite.issue(
            created_by=self.parent,
            label="Auklė",
            access_until=timezone.localdate() + timedelta(days=5),
            children=[self.child],
        )
        caregiver = CaregiverProfile.create_from_invite(invite=invite, raw_pin="9999")
        invite.used_at = timezone.now()
        invite.caregiver = caregiver
        invite.save(update_fields=["used_at", "caregiver"])
        task = Task.objects.create(title="Clean", reward=5)
        claim = TaskClaim.objects.create(
            child=self.child,
            task=task,
            task_title=task.title,
            reward_snapshot=task.reward,
            status=RequestStatus.PENDING,
        )
        self.client.force_login(caregiver.user)
        response = self.client.post(
            reverse("parent_decide_task", args=[claim.pk, "approve"])
        )
        self.assertEqual(response.status_code, 302)
        claim.refresh_from_db()
        self.assertEqual(claim.status, RequestStatus.APPROVED)
        self.assertEqual(claim.decided_by_id, caregiver.user_id)

    def test_parent_can_unlock_and_remove_caregiver(self):
        invite, _raw = CaregiverInvite.issue(
            created_by=self.parent,
            label="Senelis",
            access_until=timezone.localdate() + timedelta(days=5),
            children=[self.child],
        )
        caregiver = CaregiverProfile.create_from_invite(invite=invite, raw_pin="2222")
        invite.used_at = timezone.now()
        invite.caregiver = caregiver
        invite.save(update_fields=["used_at", "caregiver"])
        caregiver.locked_until = timezone.now() + timedelta(minutes=5)
        caregiver.save(update_fields=["locked_until"])
        self.client.force_login(self.parent)
        unlock = self.client.post(
            reverse("parent_unlock_caregiver", args=[caregiver.pk]),
            follow=True,
        )
        self.assertContains(unlock, "unlocked")
        caregiver.refresh_from_db()
        self.assertFalse(caregiver.is_locked)

        remove = self.client.post(
            reverse("parent_remove_caregiver", args=[caregiver.pk]),
            follow=True,
        )
        self.assertContains(remove, "was removed")
        caregiver.refresh_from_db()
        self.assertFalse(caregiver.is_active)
        caregiver.user.refresh_from_db()
        self.assertFalse(caregiver.user.is_active)

    def test_expired_caregiver_disappears_from_settings_list(self):
        invite, _raw = CaregiverInvite.issue(
            created_by=self.parent,
            label="Baigėsi",
            access_until=timezone.localdate() - timedelta(days=1),
            children=[self.child],
        )
        caregiver = CaregiverProfile.create_from_invite(invite=invite, raw_pin="3333")
        invite.used_at = timezone.now()
        invite.caregiver = caregiver
        invite.save(update_fields=["used_at", "caregiver"])
        self.client.force_login(self.parent)
        response = self.client.get(reverse("parent_dashboard"))
        self.assertNotContains(response, "Baigėsi")

    def test_caregiver_push_subscribe_forbidden(self):
        invite, _raw = CaregiverInvite.issue(
            created_by=self.parent,
            label="Pushless",
            access_until=timezone.localdate() + timedelta(days=3),
            children=[self.child],
        )
        caregiver = CaregiverProfile.create_from_invite(invite=invite, raw_pin="4444")
        self.client.force_login(caregiver.user)
        response = self.client.post(
            reverse("push_subscribe"),
            data=b'{"endpoint":"https://example/push","keys":{"p256dh":"x","auth":"y"}}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
