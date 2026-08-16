import io
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from economy.models import (
    ChildProfile,
    FamilySettings,
    FeedbackReport,
    FeedbackStatus,
)


@override_settings(
    EMAIL_ENABLED=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="kinkudos@example.test",
    FEEDBACK_EMAIL="owner@example.test",
)
class FeedbackWorkflowTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()
        family = FamilySettings.load()
        family.family_name = "Aurora"
        family.feedback_screenshot_retention_days = 30
        family.save(
            update_fields=[
                "family_name",
                "feedback_screenshot_retention_days",
            ]
        )
        self.parent = get_user_model().objects.create_user(
            "parent",
            password="Safe-feedback-test-123!",
        )
        self.child = ChildProfile.objects.create(
            name="Child Two",
            theme="block_world",
            theme_selected=True,
        )
        self.other_child = ChildProfile.objects.create(
            name="Child One",
            theme="magic_academy",
            theme_selected=True,
        )

    def tearDown(self):
        self.media_override.disable()
        self.media_dir.cleanup()

    @staticmethod
    def screenshot():
        image = Image.new("RGB", (2200, 1400), "#5b3e96")
        payload = io.BytesIO()
        image.save(payload, format="PNG")
        return SimpleUploadedFile(
            "screen.png",
            payload.getvalue(),
            content_type="image/png",
        )

    def login_child(self, child=None):
        session = self.client.session
        session["child_id"] = (child or self.child).pk
        session.save()

    def test_parent_feedback_is_saved_and_email_is_sent(self):
        self.client.login(username="parent", password="Safe-feedback-test-123!")

        response = self.client.post(
            reverse("submit_feedback"),
            {
                "report_type": "idea",
                "description": "Please add a weekly summary.",
                "page_path": f"{reverse('parent_dashboard')}?secret=hidden#parent-settings",
                "next": f"{reverse('parent_dashboard')}#parent-settings",
            },
            HTTP_USER_AGENT="Feedback Browser",
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        report = FeedbackReport.objects.get()
        self.assertEqual(report.parent, self.parent)
        self.assertIsNone(report.child)
        self.assertEqual(report.reporter_role, "parent")
        self.assertEqual(report.family_name, "Aurora")
        self.assertEqual(report.page_path, reverse("parent_dashboard"))
        self.assertEqual(report.app_version, "26.8.1")
        self.assertEqual(report.user_agent, "Feedback Browser")
        self.assertIsNotNone(report.email_notified_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["owner@example.test"])
        self.assertIn("Please add a weekly summary.", mail.outbox[0].body)

    def test_child_feedback_uses_child_identity_and_private_webp_screenshot(self):
        self.login_child()

        response = self.client.post(
            reverse("submit_feedback"),
            {
                "report_type": "bug",
                "description": "The mission button does not work.",
                "page_path": reverse("child_select"),
                "next": reverse("child_select"),
                "screenshot": self.screenshot(),
            },
        )

        self.assertRedirects(
            response,
            reverse("child_select"),
            fetch_redirect_response=False,
        )
        report = FeedbackReport.objects.get()
        self.assertEqual(report.child, self.child)
        self.assertIsNone(report.parent)
        self.assertEqual(report.reporter_role, "child")
        self.assertEqual(report.theme, "block_world")
        self.assertTrue(report.screenshot.name.endswith(".webp"))
        with report.screenshot.open("rb") as screenshot:
            processed = Image.open(screenshot)
            self.assertEqual(processed.format, "WEBP")
            self.assertLessEqual(max(processed.size), 1600)
            self.assertFalse(processed.getexif())

        image_url = reverse("feedback_screenshot", args=[report.pk])
        self.assertEqual(self.client.get(image_url).status_code, 200)
        self.client.session.flush()
        self.login_child(self.other_child)
        self.assertEqual(self.client.get(image_url).status_code, 404)
        self.client.session.flush()
        self.client.login(username="parent", password="Safe-feedback-test-123!")
        self.assertEqual(self.client.get(image_url).status_code, 200)

    def test_feedback_screenshot_uses_compact_lightbox_button(self):
        report = FeedbackReport.objects.create(
            report_type="idea",
            description="Suggestion with a screenshot",
            child=self.child,
            reporter_name=self.child.name,
            reporter_role="child",
            screenshot=self.screenshot(),
        )
        self.client.login(username="parent", password="Safe-feedback-test-123!")

        response = self.client.get(reverse("parent_dashboard"))
        screenshot_url = reverse("feedback_screenshot", args=[report.pk])

        self.assertContains(response, 'class="icon-button feedback-screenshot-button"')
        self.assertContains(response, f'data-evidence-full="{screenshot_url}"')
        self.assertNotContains(response, f'href="{screenshot_url}"')

    def test_parent_version_footer_is_inside_workspace_only_once(self):
        self.client.login(username="parent", password="Safe-feedback-test-123!")

        response = self.client.get(reverse("parent_dashboard"))
        content = response.content.decode()

        self.assertEqual(content.count('class="parent-version-footer"'), 1)
        self.assertNotIn('class="site-footer"', content)
        self.assertIn("Report a bug", content)
        self.assertIn("Documentation", content)
        self.assertIn('href="https://docs.kinkudos.app/"', content)
        self.assertIn('href="https://github.com/VooZ2/kinkudos/issues"', content)
        self.assertNotIn("Before posting on GitHub", content)
        self.assertIn('href="https://github.com/VooZ2/kinkudos"', content)

    @patch("economy.views.feedback.send_mail", side_effect=RuntimeError("SMTP unavailable"))
    def test_smtp_failure_does_not_lose_feedback(self, _send_mail):
        self.client.login(username="parent", password="Safe-feedback-test-123!")

        response = self.client.post(
            reverse("submit_feedback"),
            {
                "report_type": "bug",
                "description": "This report must remain saved.",
                "page_path": reverse("parent_dashboard"),
                "next": reverse("parent_dashboard"),
            },
            follow=True,
        )

        self.assertContains(
            response,
            "Feedback was saved, but the email notification could not be sent.",
        )
        report = FeedbackReport.objects.get()
        self.assertEqual(report.email_error, "RuntimeError")
        self.assertIsNone(report.email_notified_at)

    def test_submission_is_rate_limited_and_anonymous_visitors_cannot_submit(self):
        self.assertEqual(
            self.client.post(
                reverse("submit_feedback"),
                {"report_type": "bug", "description": "Anonymous report"},
            ).status_code,
            404,
        )
        self.login_child()
        for number in range(3):
            self.client.post(
                reverse("submit_feedback"),
                {
                    "report_type": "bug",
                    "description": f"Valid report number {number}",
                    "next": reverse("child_select"),
                },
            )
        response = self.client.post(
            reverse("submit_feedback"),
            {
                "report_type": "bug",
                "description": "This fourth report must be rejected.",
                "next": reverse("child_select"),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FeedbackReport.objects.count(), 3)

    def test_invalid_screenshot_is_rejected_without_saving_a_report(self):
        self.login_child()
        response = self.client.post(
            reverse("submit_feedback"),
            {
                "report_type": "bug",
                "description": "This upload is not really an image.",
                "next": reverse("child_select"),
                "screenshot": SimpleUploadedFile(
                    "fake.png",
                    b"not an image",
                    content_type="image/png",
                ),
            },
            follow=True,
        )
        self.assertContains(
            response,
            "Check the feedback description and screenshot.",
        )
        self.assertFalse(FeedbackReport.objects.exists())

    def test_parent_can_manage_feedback_but_child_cannot(self):
        report = FeedbackReport.objects.create(
            report_type="idea",
            description="A saved suggestion",
            child=self.child,
            reporter_name=self.child.name,
            reporter_role="child",
            family_name="Aurora",
            app_version="0.11.0",
        )
        self.login_child()
        status_url = reverse("parent_update_feedback_status", args=[report.pk])
        self.assertEqual(self.client.post(status_url, {"status": "resolved"}).status_code, 302)
        report.refresh_from_db()
        self.assertEqual(report.status, FeedbackStatus.NEW)

        self.client.session.flush()
        self.client.login(username="parent", password="Safe-feedback-test-123!")
        response = self.client.post(status_url, {"status": "resolved"})
        self.assertRedirects(
            response,
            f"{reverse('parent_dashboard')}#parent-settings",
            fetch_redirect_response=False,
        )
        report.refresh_from_db()
        self.assertEqual(report.status, FeedbackStatus.RESOLVED)
        dashboard = self.client.get(
            reverse("parent_dashboard"),
            {"feedback_status": "resolved", "feedback_type": "idea"},
        )
        self.assertContains(dashboard, "A saved suggestion")
        self.assertNotContains(dashboard, "feedback-launcher")

    def test_resolved_feedback_is_hidden_by_default_and_available_by_filter(self):
        FeedbackReport.objects.create(
            description="Open report",
            child=self.child,
            reporter_name=self.child.name,
            reporter_role="child",
            family_name="Aurora",
            app_version="26.1.2",
        )
        FeedbackReport.objects.create(
            description="Archived resolved report",
            status=FeedbackStatus.RESOLVED,
            child=self.child,
            reporter_name=self.child.name,
            reporter_role="child",
            family_name="Aurora",
            app_version="26.1.2",
        )
        self.client.login(username="parent", password="Safe-feedback-test-123!")

        dashboard = self.client.get(reverse("parent_dashboard"))
        self.assertContains(dashboard, "Open report")
        self.assertNotContains(dashboard, "Archived resolved report")
        self.assertContains(dashboard, 'option value="active" selected')

        resolved = self.client.get(
            reverse("parent_dashboard"),
            {"feedback_status": FeedbackStatus.RESOLVED},
        )
        self.assertNotContains(resolved, "Open report")
        self.assertContains(resolved, "Archived resolved report")

    def test_only_old_resolved_feedback_screenshots_are_removed(self):
        old_report = FeedbackReport.objects.create(
            description="Old resolved report",
            status=FeedbackStatus.RESOLVED,
            child=self.child,
            reporter_name=self.child.name,
            reporter_role="child",
            app_version="0.11.0",
        )
        old_report.screenshot.save("old.webp", self.screenshot(), save=True)
        new_report = FeedbackReport.objects.create(
            description="Unresolved report",
            child=self.child,
            reporter_name=self.child.name,
            reporter_role="child",
            app_version="0.11.0",
        )
        new_report.screenshot.save("new.webp", self.screenshot(), save=True)
        FeedbackReport.objects.filter(pk=old_report.pk).update(
            updated_at=timezone.now() - timedelta(days=31)
        )
        old_name = old_report.screenshot.name
        new_name = new_report.screenshot.name
        storage = old_report.screenshot.storage

        call_command("purge_task_evidence")

        old_report.refresh_from_db()
        new_report.refresh_from_db()
        self.assertFalse(old_report.screenshot)
        self.assertIsNotNone(old_report.screenshot_purged_at)
        self.assertFalse(storage.exists(old_name))
        self.assertTrue(new_report.screenshot)
        self.assertTrue(storage.exists(new_name))

    def test_feedback_button_is_only_visible_in_signed_in_areas(self):
        self.assertNotContains(self.client.get(reverse("home")), "feedback-launcher")
        self.login_child()
        self.assertContains(
            self.client.get(reverse("child_dashboard")),
            "feedback-launcher",
        )
        self.assertContains(
            self.client.get(reverse("child_dashboard")),
            'class="floating-actions"',
            html=False,
        )

    def test_mobile_feedback_button_avoids_parent_navigation(self):
        css = Path(settings.BASE_DIR, "static/css/app.css").read_text(
            encoding="utf-8"
        )
        self.assertIn(".floating-actions {", css)
        self.assertIn("--fab-size:", css)
        self.assertIn("--fab-gap:", css)
        self.assertIn(
            ".parent-area .floating-actions {",
            css,
        )
        self.assertIn(
            "--fab-inset-block: calc(88px + var(--safe-area-bottom));",
            css,
        )
        self.assertNotIn("--viewport-bottom-offset", css)
        self.assertIn("--fab-inset-block: calc(12px + var(--safe-area-bottom));", css)
        self.assertIn("max-height: calc(100dvh - 24px)", css)
        self.assertIn(".feedback-admin { padding: 22px; }", css)
        self.assertIn(".notice-block.notice-warning", css)
        self.assertIn('input[type="file"]::file-selector-button', css)
        self.assertIn("font: inherit", css)
        self.assertIn(".notice-block.notice-danger", css)
