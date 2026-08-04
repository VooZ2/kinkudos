from django.core.management.base import BaseCommand, CommandError

from economy.vapid import generate_vapid_keys


class Command(BaseCommand):
    help = "Sugeneruoja Web Push VAPID raktus nurodytame secrets kataloge."

    def add_arguments(self, parser):
        parser.add_argument("--output-dir", required=True)

    def handle(self, *args, **options):
        try:
            private_path, public_path = generate_vapid_keys(options["output_dir"])
        except FileExistsError:
            raise CommandError("VAPID raktai jau egzistuoja; automatiškai neperrašomi.")
        self.stdout.write(self.style.SUCCESS(f"Sukurta: {private_path}"))
        self.stdout.write(self.style.SUCCESS(f"Sukurta: {public_path}"))
