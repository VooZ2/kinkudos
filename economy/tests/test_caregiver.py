import tempfile
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from economy.models import (
    CaregiverInvite,
    CaregiverProfile,
    ChildProfile,
    FamilySettings,
    FeedbackReport,
    GoalMode,
    RequestStatus,
    SavingsGoal,
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
        self.assertContains(response, 'id="caregiver-invite-dialog"', html=False)
        self.assertContains(response, 'type="date"', html=False)

    def test_guest_invite_button_and_callout_spacing(self):
        css = Path(settings.BASE_DIR, "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn(
            ".device-pairing-actions:not(:has(form)) { grid-template-columns: minmax(0, 1fr); }",
            css,
        )
        self.assertIn(
            ".settings-section .device-pairing-actions + .account-list { margin-top: 12px; }",
            css,
        )
        callout = css[
            css.index(".feedback-email-warning,") : css.index(
                ".backup-panel .backup-warning"
            )
        ]
        self.assertIn("display: block", callout)
        self.assertIn("width: 100%", callout)
        self.assertIn("max-width: 100%", callout)
        self.assertIn("margin-inline: 0", callout)
        self.assertIn("text-align: start", callout)
        self.assertNotIn("justify-content: center", callout)
        self.assertNotIn("text-align: center", callout)
        self.assertIn(".backup-panel [data-backup-details] { width: 100%; min-width: 0; }", css)

    def test_invite_date_field_stays_inside_dialog(self):
        css = Path(settings.BASE_DIR, "static/css/app.css").read_text(encoding="utf-8")
        self.assertIn(".date-input-shell {", css)
        self.assertIn("min-width: 0 !important", css)
        self.assertIn("-webkit-appearance: none", css)
        self.assertIn(".stack-form p, .stack-form label { margin: 0; display: grid; gap: 7px; min-width: 0;", css)
        self.assertIn("max-width: 100%;", css.split(".action-dialog {")[-1].split("}")[0])
        self.client.force_login(self.parent)
        response = self.client.get(reverse("parent_dashboard"))
        html = response.content.decode()
        start = html.index('id="caregiver-invite-dialog"')
        dialog_html = html[start : html.index("</dialog>", start)]
        self.assertIn('class="date-input-shell"', dialog_html)
        self.assertIn('id="id_caregiver_invite_access_until"', dialog_html)
        self.assertLess(
            dialog_html.index('class="date-input-shell"'),
            dialog_html.index('id="id_caregiver_invite_access_until"'),
        )

    def test_active_guest_row_uses_copy_text(self):
        invite, _raw = CaregiverInvite.issue(
            created_by=self.parent,
            label="Senelė Ona",
            access_until=timezone.localdate() + timedelta(days=10),
            children=[self.child],
        )
        caregiver = CaregiverProfile.create_from_invite(invite=invite, raw_pin="1111")
        invite.used_at = timezone.now()
        invite.caregiver = caregiver
        invite.save(update_fields=["used_at", "caregiver"])
        self.client.force_login(self.parent)
        response = self.client.get(reverse("parent_dashboard"))
        html = response.content.decode()
        start = html.index("data-copy-caregiver-login")
        snippet = html[max(0, start - 280) : start + 220]
        self.assertIn('class="share-copy-button"', snippet)
        self.assertIn(">Copy<", snippet)
        self.assertNotIn("icon-clipboard-check", snippet)
        self.assertNotIn("Copy sign-in link", snippet)

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
        self.assertContains(response, ">Copy<", html=False)
        self.assertContains(response, 'href="#icon-share-nodes"', html=False)
        self.assertNotContains(response, "is ready to share")
        self.assertNotContains(response, 'data-share-caregiver-invite hidden')
        self.assertContains(response, "dialog.showModal")
        self.assertContains(response, "Invite link:")
        html = response.content.decode()
        dialog_html = html[
            html.index('id="caregiver-invite-share-dialog"') : html.index(
                'id="push-help-dialog"'
            )
        ]
        self.assertIn("<span>Invite link:</span>", dialog_html)
        self.assertIn(">Copy<", dialog_html)
        self.assertNotIn("#icon-clipboard-check", dialog_html)
        self.assertNotIn("Copy link", dialog_html)
        self.assertLess(
            dialog_html.index("share-dialog-toolbar"),
            dialog_html.index("danger-warning"),
        )
        self.assertLess(
            dialog_html.index("danger-warning"),
            dialog_html.index("dialog-actions"),
        )
        css = Path(settings.BASE_DIR, "static/css/app.css").read_text(encoding="utf-8")
        label_rule = css[
            css.index(".share-dialog > label {") : css.index(
                "}", css.index(".share-dialog > label {")
            )
        ]
        self.assertIn("display: grid", label_rule)
        self.assertIn("gap: 10px", label_rule)
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

    def test_expired_caregiver_cannot_fall_back_to_parent_scope(self):
        invite, _raw = CaregiverInvite.issue(
            created_by=self.parent,
            label="Pasibaigė",
            access_until=timezone.localdate() - timedelta(days=1),
            children=[self.child],
        )
        caregiver = CaregiverProfile.create_from_invite(invite=invite, raw_pin="9999")
        self.client.force_login(caregiver.user)

        response = self.client.post(
            reverse("parent_remove_child_account", args=[self.other_child.pk])
        )

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.child.refresh_from_db()
        self.other_child.refresh_from_db()
        caregiver.refresh_from_db()
        caregiver.user.refresh_from_db()
        self.assertTrue(self.child.is_active)
        self.assertTrue(self.other_child.is_active)
        self.assertFalse(caregiver.is_active)
        self.assertFalse(caregiver.user.is_active)

    def test_caregiver_media_is_limited_to_assigned_children(self):
        invite, _raw = CaregiverInvite.issue(
            created_by=self.parent,
            label="Auklė",
            access_until=timezone.localdate() + timedelta(days=5),
            children=[self.child],
        )
        caregiver = CaregiverProfile.create_from_invite(invite=invite, raw_pin="9999")
        task = Task.objects.create(title="Photo task", reward=5)
        own_claim = TaskClaim.objects.create(
            child=self.child,
            task=task,
            task_title=task.title,
            reward_snapshot=task.reward,
            status=RequestStatus.PENDING,
        )
        other_claim = TaskClaim.objects.create(
            child=self.other_child,
            task=task,
            task_title=task.title,
            reward_snapshot=task.reward,
            status=RequestStatus.PENDING,
        )
        own_report = FeedbackReport.objects.create(
            child=self.child,
            description="Own screenshot",
            reporter_name=self.child.name,
            reporter_role="child",
            app_version="26.8.0",
        )
        other_report = FeedbackReport.objects.create(
            child=self.other_child,
            description="Other screenshot",
            reporter_name=self.other_child.name,
            reporter_role="child",
            app_version="26.8.0",
        )
        parent_report = FeedbackReport.objects.create(
            parent=self.parent,
            description="Parent screenshot",
            reporter_name=self.parent.username,
            reporter_role="parent",
            app_version="26.8.0",
        )

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                self.child.avatar = SimpleUploadedFile(
                    "own.webp", b"own-avatar", content_type="image/webp"
                )
                self.other_child.avatar = SimpleUploadedFile(
                    "other.webp", b"other-avatar", content_type="image/webp"
                )
                self.child.save(update_fields=["avatar"])
                self.other_child.save(update_fields=["avatar"])
                own_claim.evidence_image = SimpleUploadedFile(
                    "own-evidence.webp", b"own-evidence", content_type="image/webp"
                )
                other_claim.evidence_image = SimpleUploadedFile(
                    "other-evidence.webp", b"other-evidence", content_type="image/webp"
                )
                own_claim.save(update_fields=["evidence_image"])
                other_claim.save(update_fields=["evidence_image"])
                own_report.screenshot = SimpleUploadedFile(
                    "own-feedback.webp", b"own-feedback", content_type="image/webp"
                )
                other_report.screenshot = SimpleUploadedFile(
                    "other-feedback.webp", b"other-feedback", content_type="image/webp"
                )
                parent_report.screenshot = SimpleUploadedFile(
                    "parent-feedback.webp", b"parent-feedback", content_type="image/webp"
                )
                own_report.save(update_fields=["screenshot"])
                other_report.save(update_fields=["screenshot"])
                parent_report.save(update_fields=["screenshot"])

                self.client.force_login(caregiver.user)
                dashboard = self.client.get(reverse("parent_dashboard"))
                self.assertEqual(
                    [report.pk for report in dashboard.context["feedback_page"].object_list],
                    [own_report.pk],
                )
                allowed_urls = [
                    reverse("child_avatar", args=[self.child.pk]),
                    reverse("task_evidence", args=[own_claim.pk, "full"]),
                    reverse("feedback_screenshot", args=[own_report.pk]),
                ]
                denied_urls = [
                    reverse("child_avatar", args=[self.other_child.pk]),
                    reverse("task_evidence", args=[other_claim.pk, "full"]),
                    reverse("feedback_screenshot", args=[other_report.pk]),
                    reverse("feedback_screenshot", args=[parent_report.pk]),
                ]
                for url in allowed_urls:
                    with self.subTest(url=url, access="allowed"):
                        self.assertEqual(self.client.get(url).status_code, 200)
                for url in denied_urls:
                    with self.subTest(url=url, access="denied"):
                        self.assertEqual(self.client.get(url).status_code, 404)

    def test_caregiver_cannot_post_manage_goal_actions(self):
        invite, _raw = CaregiverInvite.issue(
            created_by=self.parent,
            label="Senelis",
            access_until=timezone.localdate() + timedelta(days=5),
            children=[self.child],
        )
        caregiver = CaregiverProfile.create_from_invite(invite=invite, raw_pin="9999")
        goal = SavingsGoal.objects.create(
            child=self.child,
            title="Bicycle",
            target_amount=100,
            mode=GoalMode.SAVED,
        )
        self.client.force_login(caregiver.user)
        actions = [
            ("parent_add_goal_points", {},),
            ("parent_return_goal_points", {},),
            (
                "parent_edit_goal",
                {"title": "Changed", "target_amount": "200", "icon": "⭐"},
            ),
            ("parent_close_goal", {},),
            ("parent_delete_goal", {},),
        ]

        for name, data in actions:
            with self.subTest(action=name):
                response = self.client.post(
                    reverse(name, args=[goal.pk]),
                    data,
                )
                self.assertRedirects(
                    response,
                    reverse("parent_dashboard"),
                    fetch_redirect_response=False,
                )

        goal.refresh_from_db()
        self.assertEqual(goal.title, "Bicycle")
        self.assertEqual(goal.target_amount, 100)
        self.assertEqual(goal.status, "active")

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
