from django.core.management.base import BaseCommand

from economy.models import FamilySettings


class Command(BaseCommand):
    help = "Disable the application-level IP allowlist."

    def handle(self, *args, **options):
        family = FamilySettings.load()
        family.network_access_mode = FamilySettings.NetworkAccessMode.OPEN
        family.allowed_networks = ""
        family.save(update_fields=["network_access_mode", "allowed_networks"])
        self.stdout.write(self.style.SUCCESS("Network restrictions disabled."))
