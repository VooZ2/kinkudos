import getpass
import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import translation
from django.utils.translation import gettext as _

from economy.models import ChildProfile, FamilySettings, Reward, Task, Theme


class Command(BaseCommand):
    help = "Interactively creates the first parent account and child profiles."

    def add_arguments(self, parser):
        parser.add_argument("--language", choices=("en", "lt"), default="en")
        parser.add_argument("--parent-username", default="parents")

    def prompt_password(self, label, validator=None):
        first = getpass.getpass(label)
        second = getpass.getpass(_("Repeat: "))
        if first != second:
            raise CommandError(_("The values do not match."))
        if validator:
            try:
                validator(first)
            except ValidationError as exc:
                raise CommandError(" ".join(exc.messages)) from exc
        return first

    @transaction.atomic
    def handle(self, *args, **options):
        with translation.override(options["language"]):
            User = get_user_model()
            username = input(
                _("Parent username [%(default)s]: ") % {"default": options["parent_username"]}
            ).strip() or options["parent_username"]
            if User.objects.filter(username=username).exists():
                raise CommandError(_("User %(username)s already exists.") % {"username": username})

            email = input(_("Parent email address (optional): ")).strip()
            password = self.prompt_password(
                _("New parent password: "),
                validator=validate_password,
            )
            family = FamilySettings.load()
            family_name = input(_("Family name or nickname: ")).strip()
            if not family_name:
                raise CommandError(_("The family name or nickname is required."))
            family.family_name = family_name
            family.currency_name = "Points"
            family.default_min_balance = -100
            recovery_code = secrets.token_urlsafe(24)
            family.recovery_code_hash = make_password(recovery_code)
            family.save()

            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True,
            )

            raw_count = input(_("Number of child profiles [1]: ")).strip() or "1"
            try:
                child_count = int(raw_count)
            except ValueError as exc:
                raise CommandError(_("The number of child profiles must be a number.")) from exc
            if not 1 <= child_count <= 20:
                raise CommandError(_("Choose between 1 and 20 child profiles."))

            for number in range(1, child_count + 1):
                name = input(_("Child %(number)s name: ") % {"number": number}).strip()
                if not name:
                    raise CommandError(_("The child's name is required."))
                pin = self.prompt_password(
                    _("%(name)s 4-digit PIN: ") % {"name": name},
                    validator=self.validate_pin,
                )
                child = ChildProfile(
                    name=name,
                    theme=Theme.NEUTRAL,
                    theme_selected=False,
                    min_balance=family.default_min_balance,
                )
                child.set_pin(pin)
                child.save()

            Task.objects.get_or_create(
                title=_("Tidy your room"),
                defaults={"reward": 30, "icon": "🛏️"},
            )
            Reward.objects.get_or_create(
                title=_("One extra hour of screen time"),
                defaults={"cost": 100, "icon": "📱"},
            )

            self.stdout.write(self.style.SUCCESS(_("Family created.")))
            self.stdout.write(_("One-time recovery code (save it in your password manager):"))
            self.stdout.write(self.style.WARNING(recovery_code))
            self.stdout.write(_("This code will not be shown again."))

    @staticmethod
    def validate_pin(value):
        if not (len(value) == 4 and value.isdigit()):
            raise ValidationError(_("The PIN must contain exactly 4 digits."))
