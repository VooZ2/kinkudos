from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from economy.models import (
    FamilySettings,
    FeedbackReport,
    FeedbackStatus,
    RequestStatus,
    TaskClaim,
)
from economy.push import notify_birthday_award
from economy.services import award_birthdays, randomize_daily_themes


class Command(BaseCommand):
    help = (
        "Delete expired task evidence and resolved feedback screenshots while "
        "preserving text history."
    )

    def handle(self, *args, **options):
        birthday_awards = award_birthdays()
        for award in birthday_awards:
            notify_birthday_award(award)
        self.stdout.write(
            self.style.SUCCESS(
                f"Awarded {len(birthday_awards)} birthday gift(s)."
            )
        )

        changed_themes = randomize_daily_themes()
        self.stdout.write(
            self.style.SUCCESS(
                f"Randomized themes for {len(changed_themes)} child profile(s)."
            )
        )

        retention_days = FamilySettings.load().evidence_retention_days
        if retention_days == FamilySettings.EvidenceRetention.FOREVER:
            self.stdout.write("Task evidence retention is unlimited; nothing to purge.")
        else:
            cutoff = timezone.now() - timedelta(days=retention_days)
            claims = TaskClaim.objects.filter(
                Q(evidence_image__gt="") | Q(evidence_thumbnail__gt=""),
                status__in=[
                    RequestStatus.APPROVED,
                    RequestStatus.REJECTED,
                    RequestStatus.CANCELLED,
                ],
                decided_at__lt=cutoff,
            )
            removed = 0
            for claim in claims.iterator():
                files = [
                    (claim.evidence_image.storage, claim.evidence_image.name)
                    if claim.evidence_image
                    else None,
                    (claim.evidence_thumbnail.storage, claim.evidence_thumbnail.name)
                    if claim.evidence_thumbnail
                    else None,
                ]
                claim.evidence_image = ""
                claim.evidence_thumbnail = ""
                claim.evidence_purged_at = timezone.now()
                claim.save(
                    update_fields=[
                        "evidence_image",
                        "evidence_thumbnail",
                        "evidence_purged_at",
                    ]
                )
                for file_info in files:
                    if file_info:
                        storage, name = file_info
                        storage.delete(name)
                removed += 1

            self.stdout.write(
                self.style.SUCCESS(f"Purged evidence from {removed} task claim(s).")
            )

        feedback_retention_days = (
            FamilySettings.load().feedback_screenshot_retention_days
        )
        if feedback_retention_days == FamilySettings.EvidenceRetention.FOREVER:
            self.stdout.write("Feedback screenshot retention is unlimited.")
            return

        feedback_cutoff = timezone.now() - timedelta(days=feedback_retention_days)
        reports = FeedbackReport.objects.filter(
            screenshot__gt="",
            status=FeedbackStatus.RESOLVED,
            updated_at__lt=feedback_cutoff,
        )
        feedback_removed = 0
        for report in reports.iterator():
            storage = report.screenshot.storage
            name = report.screenshot.name
            report.screenshot = ""
            report.screenshot_purged_at = timezone.now()
            report.save(
                update_fields=["screenshot", "screenshot_purged_at", "updated_at"]
            )
            storage.delete(name)
            feedback_removed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Purged screenshots from {feedback_removed} feedback report(s)."
            )
        )
