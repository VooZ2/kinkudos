from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from economy.lottery import send_due_lottery_reminders
from economy.models import FamilySettings
from economy.services import run_due_assignment_presets, send_due_assigned_task_nudges


class Command(BaseCommand):
    help = (
        "Send due weekly lottery reminders and soft assigned-task nudges, "
        "and run due assignment presets."
    )

    def handle(self, *args, **options):
        timezone.activate(FamilySettings.load().timezone_name or settings.TIME_ZONE)
        try:
            lottery_sent = send_due_lottery_reminders()
            nudge_sent = send_due_assigned_task_nudges()
            preset_batches = run_due_assignment_presets()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Sent {len(lottery_sent)} lottery reminder(s), "
                    f"{len(nudge_sent)} assigned-task nudge(s), "
                    f"and created {len(preset_batches)} preset assignment(s)."
                )
            )
        finally:
            timezone.deactivate()
