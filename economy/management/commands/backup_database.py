import sqlite3
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Sukuria nuoseklią SQLite online backup kopiją."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            default=str(Path(settings.BASE_DIR) / "backups"),
        )

    def handle(self, *args, **options):
        if connection.vendor != "sqlite":
            raise CommandError("Ši komanda skirta SQLite.")
        source_path = Path(connection.settings_dict["NAME"])
        if not source_path.exists():
            raise CommandError(f"Duomenų bazė nerasta: {source_path}")
        output_dir = Path(options["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / f"kinkudos-{datetime.now():%Y%m%d-%H%M%S}.sqlite3"

        source = sqlite3.connect(source_path)
        target = sqlite3.connect(destination)
        try:
            source.backup(target)
            result = target.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                destination.unlink(missing_ok=True)
                raise CommandError(f"Kopijos patikra nepavyko: {result}")
        finally:
            target.close()
            source.close()
        self.stdout.write(self.style.SUCCESS(str(destination)))

