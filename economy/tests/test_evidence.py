import io
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from economy.models import ChildProfile, FamilySettings, LedgerEntry, RequestStatus, Task, TaskClaim
from economy.services import approve_task_claim


class TaskEvidenceWorkflowTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()
        self.parent = get_user_model().objects.create_user(
            "parent",
            password="Safe-visual-test-123!",
            is_staff=True,
        )
        self.child = ChildProfile.objects.create(
            name="Child Two",
            theme="block_world",
            theme_selected=True,
        )
        self.child.set_pin("1234")
        self.child.save(update_fields=["pin_hash"])
        self.task = Task.objects.create(title="Tidy room", reward=20, icon="🧹")
        family = FamilySettings.load()
        family.photo_bonus_points = 5
        family.save(update_fields=["photo_bonus_points"])
        session = self.client.session
        session["child_id"] = self.child.pk
        session.save()

    def tearDown(self):
        self.media_override.disable()
        self.media_dir.cleanup()

    @staticmethod
    def photo():
        image = Image.new("RGB", (1600, 900), "#78a06d")
        payload = io.BytesIO()
        image.save(payload, format="JPEG", exif=b"test metadata")
        return SimpleUploadedFile(
            "proof.jpg",
            payload.getvalue(),
            content_type="image/jpeg",
        )

    def test_photo_is_converted_and_bonus_is_snapshotted(self):
        response = self.client.post(
            reverse("child_submit_task", args=[self.task.pk]),
            {"proof": self.photo()},
        )
        self.assertRedirects(response, reverse("child_dashboard"))
        claim = TaskClaim.objects.get()
        self.assertEqual(claim.photo_bonus_snapshot, 5)
        self.assertTrue(claim.evidence_image.name.endswith(".webp"))
        self.assertTrue(claim.evidence_thumbnail.name.endswith(".webp"))
        with claim.evidence_image.open("rb") as evidence:
            processed = Image.open(evidence)
            self.assertEqual(processed.format, "WEBP")
            self.assertLessEqual(max(processed.size), 1280)
            self.assertFalse(processed.getexif())

    def test_enhanced_task_submit_returns_success_effect_after_server_accepts_it(self):
        response = self.client.post(
            reverse("child_submit_task", args=[self.task.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "ok": True,
                "redirect_url": reverse("child_dashboard"),
                "effect": "task",
            },
        )
        self.assertEqual(TaskClaim.objects.filter(status=RequestStatus.PENDING).count(), 1)

    def test_enhanced_duplicate_submit_does_not_return_success_effect(self):
        self.client.post(reverse("child_submit_task", args=[self.task.pk]))

        response = self.client.post(
            reverse("child_submit_task", args=[self.task.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "ok": False,
                "redirect_url": reverse("child_dashboard"),
            },
        )

    def test_child_task_forms_enable_server_confirmed_success_effect(self):
        response = self.client.get(reverse("child_dashboard"))

        self.assertContains(response, 'data-success-effect="task"')

    def test_only_own_child_or_parent_can_open_evidence(self):
        self.client.post(
            reverse("child_submit_task", args=[self.task.pk]),
            {"proof": self.photo()},
        )
        claim = TaskClaim.objects.get()
        response = self.client.get(reverse("task_evidence", args=[claim.pk, "thumbnail"]))
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        self.client.session.flush()
        self.assertEqual(
            self.client.get(reverse("task_evidence", args=[claim.pk, "full"])).status_code,
            404,
        )
        self.client.login(username="parent", password="Safe-visual-test-123!")
        self.assertEqual(
            self.client.get(reverse("task_evidence", args=[claim.pk, "full"])).status_code,
            200,
        )

    def test_parent_can_request_revision_and_child_can_resubmit(self):
        self.client.post(reverse("child_submit_task", args=[self.task.pk]))
        claim = TaskClaim.objects.get()
        self.client.logout()
        self.client.login(username="parent", password="Safe-visual-test-123!")
        self.client.post(
            reverse("parent_decide_task", args=[claim.pk, "revise"]),
            {"reason": "Please clean under the bed."},
        )
        claim.refresh_from_db()
        self.assertEqual(claim.status, RequestStatus.NEEDS_CHANGES)
        self.assertEqual(claim.revision_note, "Please clean under the bed.")

        self.client.logout()
        session = self.client.session
        session["child_id"] = self.child.pk
        session.save()
        self.client.post(
            reverse("child_resubmit_task", args=[claim.pk]),
            {"proof": self.photo()},
        )
        claim.refresh_from_db()
        self.assertEqual(claim.status, RequestStatus.PENDING)
        self.assertEqual(claim.revision_note, "")
        self.assertTrue(claim.evidence_image)

    def test_task_decision_uses_compact_icon_actions_and_optional_dialog_comment(self):
        self.client.post(
            reverse("child_submit_task", args=[self.task.pk]),
            {"proof": self.photo()},
        )
        claim = TaskClaim.objects.get()
        self.client.logout()
        self.client.login(username="parent", password="Safe-visual-test-123!")

        response = self.client.get(reverse("parent_dashboard"))

        self.assertContains(response, 'class="evidence-thumb-button"', html=False)
        self.assertContains(response, 'class="decision-icon-button decision-approve"', html=False)
        self.assertContains(response, f'id="revise-task-{claim.pk}"', html=False)
        self.assertContains(response, f'id="reject-task-{claim.pk}"', html=False)
        self.assertContains(response, 'id="evidence-lightbox"', html=False)
        self.assertContains(response, "data-lightbox-image", html=False)
        self.assertNotContains(response, "data-evidence-lightbox-image", html=False)
        self.assertNotContains(response, 'placeholder="Atmetimo priežastis" required', html=False)

    def test_rejection_comment_is_visible_to_child(self):
        self.client.post(reverse("child_submit_task", args=[self.task.pk]))
        claim = TaskClaim.objects.get()
        self.client.logout()
        self.client.login(username="parent", password="Safe-visual-test-123!")
        self.client.post(
            reverse("parent_decide_task", args=[claim.pk, "reject"]),
            {"reason": "Prašau pakloti ir pagalvę."},
        )
        self.client.logout()
        session = self.client.session
        session["child_id"] = self.child.pk
        session.save()

        response = self.client.get(reverse("child_dashboard"))

        self.assertContains(response, "Prašau pakloti ir pagalvę.")
        self.assertContains(response, "Parent response")

    def test_revision_comment_may_be_empty(self):
        self.client.post(reverse("child_submit_task", args=[self.task.pk]))
        claim = TaskClaim.objects.get()
        self.client.logout()
        self.client.login(username="parent", password="Safe-visual-test-123!")

        response = self.client.post(
            reverse("parent_decide_task", args=[claim.pk, "revise"]),
            {"reason": ""},
        )

        self.assertRedirects(response, reverse("parent_dashboard"))
        claim.refresh_from_db()
        self.assertEqual(claim.status, RequestStatus.NEEDS_CHANGES)
        self.assertEqual(claim.revision_note, "")

    def test_cleanup_removes_expired_files_but_keeps_history(self):
        self.client.post(
            reverse("child_submit_task", args=[self.task.pk]),
            {"proof": self.photo()},
        )
        claim = TaskClaim.objects.get()
        approve_task_claim(claim=claim, actor=self.parent)
        old_decision = timezone.now() - timedelta(days=31)
        TaskClaim.objects.filter(pk=claim.pk).update(decided_at=old_decision)
        full_name = claim.evidence_image.name
        thumbnail_name = claim.evidence_thumbnail.name
        storage = claim.evidence_image.storage

        call_command("purge_task_evidence")

        claim.refresh_from_db()
        self.assertFalse(claim.evidence_image)
        self.assertFalse(claim.evidence_thumbnail)
        self.assertIsNotNone(claim.evidence_purged_at)
        self.assertFalse(storage.exists(full_name))
        self.assertFalse(storage.exists(thumbnail_name))
        self.assertTrue(TaskClaim.objects.filter(pk=claim.pk).exists())
        self.assertTrue(LedgerEntry.objects.filter(source_id=claim.pk).exists())
