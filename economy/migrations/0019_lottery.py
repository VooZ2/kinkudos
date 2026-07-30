# ruff: noqa: RUF012

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("economy", "0018_assigned_tasks"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ledgerentry",
            name="kind",
            field=models.CharField(
                choices=[
                    ("task", "Task"),
                    ("assigned_task", "Assigned task"),
                    ("penalty", "Penalty"),
                    ("reward", "Reward"),
                    ("lottery", "Lottery"),
                    ("adjustment", "Adjustment"),
                    ("gift", "Gift"),
                    ("birthday", "Birthday"),
                ],
                max_length=16,
            ),
        ),
        migrations.CreateModel(
            name="LotteryTicket",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("week_start", models.DateField()),
                ("values", models.JSONField()),
                ("prize_amount", models.IntegerField()),
                ("applied_delta", models.IntegerField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("open", "Open"), ("revealed", "Revealed")],
                        default="open",
                        max_length=12,
                    ),
                ),
                ("purchased_at", models.DateTimeField(auto_now_add=True)),
                ("revealed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "child",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lottery_tickets",
                        to="economy.childprofile",
                    ),
                ),
                (
                    "purchase_ledger_entry",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lottery_ticket_purchase",
                        to="economy.ledgerentry",
                    ),
                ),
                (
                    "result_ledger_entry",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lottery_ticket_result",
                        to="economy.ledgerentry",
                    ),
                ),
            ],
            options={
                "ordering": ["-purchased_at", "-pk"],
            },
        ),
        migrations.CreateModel(
            name="LotteryReminder",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("week_start", models.DateField()),
                ("scheduled_for", models.DateTimeField()),
                ("handled_at", models.DateTimeField(blank=True, null=True)),
                ("sent", models.BooleanField(default=False)),
                (
                    "child",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lottery_reminders",
                        to="economy.childprofile",
                    ),
                ),
            ],
            options={
                "ordering": ["-week_start", "-pk"],
            },
        ),
        migrations.AddConstraint(
            model_name="lotteryticket",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "open")),
                fields=("child",),
                name="one_open_lottery_ticket_per_child",
            ),
        ),
        migrations.AddIndex(
            model_name="lotteryticket",
            index=models.Index(
                fields=["child", "week_start"],
                name="lottery_child_week_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="lotteryreminder",
            constraint=models.UniqueConstraint(
                fields=("child", "week_start"),
                name="one_lottery_reminder_per_child_week",
            ),
        ),
    ]
