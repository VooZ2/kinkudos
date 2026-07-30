import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from economy.models import FamilySettings


class Command(BaseCommand):
    help = "Interaktyviai atkuria tėvų slaptažodį patikrinus vienkartinį atkūrimo kodą."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="tevai")

    def handle(self, *args, **options):
        family = FamilySettings.load()
        code = getpass.getpass("Atkūrimo kodas: ")
        if not family.recovery_code_hash or not check_password(code, family.recovery_code_hash):
            raise CommandError("Neteisingas atkūrimo kodas.")

        password = getpass.getpass("Naujas tėvų slaptažodis: ")
        repeat = getpass.getpass("Pakartokite: ")
        if password != repeat:
            raise CommandError("Slaptažodžiai nesutampa.")
        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from exc

        User = get_user_model()
        try:
            user = User.objects.get(username=options["username"])
        except User.DoesNotExist as exc:
            raise CommandError("Tėvų paskyra nerasta.") from exc
        user.set_password(password)
        user.save(update_fields=["password"])
        self.stdout.write(self.style.SUCCESS("Slaptažodis pakeistas; senos sesijos nebegalios."))

