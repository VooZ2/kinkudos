from datetime import timedelta

from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from economy.models import AttemptCounter, DevicePairingLink


class Command(BaseCommand):
    help = "Run all daily KinKudos maintenance tasks."

    def handle(self, *args, **options):
        call_command("purge_task_evidence")
        cutoff = timezone.now() - timedelta(days=1)
        counters, _ = AttemptCounter.objects.filter(window_start__lt=cutoff).delete()
        links, _ = DevicePairingLink.objects.filter(
            expires_at__lt=timezone.now(),
        ).delete()
        Session.objects.clear_expired()
        self.stdout.write(
            self.style.SUCCESS(
                f"Removed {counters} attempt counter row(s) and "
                f"{links} expired pairing link row(s)."
            )
        )
