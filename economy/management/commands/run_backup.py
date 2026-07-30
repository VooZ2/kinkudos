import time
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from economy.backups import backup_status, request_manual_backup


class Command(BaseCommand):
    help = "Requests an external KinKudos backup and waits for completion."

    def handle(self, *args, **options):
        started_at = timezone.now()
        try:
            request_manual_backup()
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc
        deadline = started_at + timedelta(hours=1)
        while timezone.now() < deadline:
            time.sleep(2)
            status = backup_status()
            if status.get("running"):
                continue
            if status.get("last_success") and status["last_success"] >= started_at:
                self.stdout.write(self.style.SUCCESS("Backup completed successfully."))
                return
            raise CommandError(status.get("error") or "Backup failed.")
        raise CommandError("Backup did not finish within one hour.")
