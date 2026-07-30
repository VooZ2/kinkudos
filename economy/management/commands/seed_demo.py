from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from economy.models import (
    ChildProfile,
    FamilySettings,
    LedgerKind,
    PenaltyTemplate,
    Proposal,
    ProposalType,
    Reward,
    Task,
    Theme,
)
from economy.services import post_ledger_entry, submit_reward_request, submit_task


class Command(BaseCommand):
    help = "Sukuria tik vietinei demonstracijai skirtus duomenis."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Demonstracinius duomenis leidžiama kurti tik DEBUG režimu.")
        User = get_user_model()
        if User.objects.exists() or ChildProfile.objects.exists():
            raise CommandError("Duomenų bazė nėra tuščia; niekas nepakeista.")

        parent = User.objects.create_user(
            username="tevai",
            password="Demo-safe-pass-123!",
            is_staff=True,
        )
        family = FamilySettings.load()
        family.default_min_balance = -100
        family.save(update_fields=["default_min_balance"])

        gabija = ChildProfile(
            name="Gabija",
            theme=Theme.MAGIC_ACADEMY,
            min_balance=-100,
        )
        gabija.set_pin("1234")
        gabija.save()
        augustas = ChildProfile(
            name="Augustas",
            theme=Theme.BLOCK_WORLD,
            min_balance=-100,
        )
        augustas.set_pin("5678")
        augustas.save()

        tasks = [
            Task.objects.create(title="Sutvarkyti savo kambarį", reward=30, icon="🛏️"),
            Task.objects.create(title="Sukrauti indus", reward=20, icon="🍽️"),
            Task.objects.create(title="Perskaityti 20 puslapių", reward=25, icon="📚"),
            Task.objects.create(title="Pasirūpinti augintiniu", reward=15, icon="🐾"),
        ]
        Reward.objects.create(title="Papildoma valanda ekrano", cost=100, icon="📱")
        reward = Reward.objects.create(title="Šeimos kino vakaras", cost=180, icon="⭐")
        PenaltyTemplate.objects.create(title="Neatliktas susitarimas", amount=-20, icon="📚")

        post_ledger_entry(
            child=gabija,
            delta=140,
            kind=LedgerKind.ADJUSTMENT,
            description="Demonstracinis pradinis balansas",
            actor=parent,
        )
        post_ledger_entry(
            child=augustas,
            delta=85,
            kind=LedgerKind.ADJUSTMENT,
            description="Demonstracinis pradinis balansas",
            actor=parent,
        )
        submit_task(child=gabija, task=tasks[0])
        submit_reward_request(child=augustas, reward=reward)
        Proposal.objects.create(
            child=gabija,
            proposal_type=ProposalType.GOAL,
            title="Nauja knyga",
            suggested_cost=250,
            icon="📚",
        )
        self.stdout.write(self.style.SUCCESS("Demonstraciniai duomenys sukurti."))
        self.stdout.write("Tėvai: tevai / Demo-safe-pass-123!")
        self.stdout.write("Gabija PIN: 1234; Augustas PIN: 5678")
