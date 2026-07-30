import secrets

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from economy.models import FamilySettings


class Command(BaseCommand):
    help = "Pakeičia tėvų paskyros atkūrimo kodą ir parodo jį vieną kartą."

    def handle(self, *args, **options):
        code = secrets.token_urlsafe(24)
        family = FamilySettings.load()
        family.recovery_code_hash = make_password(code)
        family.save(update_fields=["recovery_code_hash"])
        self.stdout.write("Naujas atkūrimo kodas:")
        self.stdout.write(self.style.WARNING(code))
        self.stdout.write("Išsaugokite jį slaptažodžių tvarkyklėje.")

