from django.core.management.base import BaseCommand

from economy.lottery import send_due_lottery_reminders


class Command(BaseCommand):
    help = "Send due weekly lottery reminders to eligible child devices."

    def handle(self, *args, **options):
        sent = send_due_lottery_reminders()
        self.stdout.write(
            self.style.SUCCESS(f"Sent {len(sent)} lottery reminder(s).")
        )
