from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from economy.models import (
    ChildProfile,
    FamilySettings,
    GoalMode,
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

        child_one = ChildProfile(
            name="Child One",
            theme=Theme.MAGIC_ACADEMY,
            min_balance=-100,
        )
        child_one.set_pin("1234")
        child_one.save()
        child_two = ChildProfile(
            name="Child Two",
            theme=Theme.BLOCK_WORLD,
            min_balance=-100,
        )
        child_two.set_pin("5678")
        child_two.save()

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
            child=child_one,
            delta=140,
            kind=LedgerKind.ADJUSTMENT,
            description="Demonstracinis pradinis balansas",
            actor=parent,
        )
        post_ledger_entry(
            child=child_two,
            delta=85,
            kind=LedgerKind.ADJUSTMENT,
            description="Demonstracinis pradinis balansas",
            actor=parent,
        )
        submit_task(child=child_one, task=tasks[0])
        submit_reward_request(child=child_two, reward=reward)
        Proposal.objects.create(
            child=child_one,
            proposal_type=ProposalType.GOAL,
            title="Nauja knyga",
            suggested_cost=250,
            icon="📚",
            goal_mode=GoalMode.AVAILABLE,
        )
        self.stdout.write(self.style.SUCCESS("Demonstraciniai duomenys sukurti."))
        self.stdout.write("Tėvai: tevai / Demo-safe-pass-123!")
        self.stdout.write("Child One PIN: 1234; Child Two PIN: 5678")
