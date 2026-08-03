from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from economy.lottery import send_due_lottery_reminders
from economy.models import FamilySettings


class Command(BaseCommand):
    help = "Send due weekly lottery reminders to eligible child devices."

    def handle(self, *args, **options):
        timezone.activate(FamilySettings.load().timezone_name or settings.TIME_ZONE)
        try:
            sent = send_due_lottery_reminders()
            self.stdout.write(
                self.style.SUCCESS(f"Sent {len(sent)} lottery reminder(s).")
            )
        finally:
            timezone.deactivate()
