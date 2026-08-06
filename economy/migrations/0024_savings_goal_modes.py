from django.conf import settings
from django.db import migrations, models


# Existing children with exactly one active goal can keep that goal's balance-based
# progress; children with multiple goals remain unselected until they choose a mode.
import django.db.models.deletion


def select_safe_current_goals(apps, schema_editor):
    SavingsGoal = apps.get_model("economy", "SavingsGoal")
    child_ids = (
        SavingsGoal.objects.filter(status="active")
        .values_list("child_id", flat=True)
        .distinct()
    )
    for child_id in child_ids:
        goals = list(
            SavingsGoal.objects.filter(child_id=child_id, status="active").order_by("pk")
        )
        if len(goals) == 1:
            goals[0].mode = "available"
            goals[0].save(update_fields=["mode"])


class Migration(migrations.Migration):
    dependencies = [("economy", "0023_browser_setup")]

    operations = [
        migrations.AddField(
            model_name="savingsgoal",
            name="mode",
            field=models.CharField(
                blank=True,
                choices=[("available", "Current goal"), ("saved", "Saved")],
                max_length=16,
                null=True,
            ),
        ),
        migrations.AddConstraint(
            model_name="savingsgoal",
            constraint=models.CheckConstraint(
                condition=models.Q(("target_amount__gt", 0)),
                name="savings_goal_positive_target",
            ),
        ),
        migrations.CreateModel(
            name="SavingsContribution",
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
                ("amount", models.PositiveIntegerField()),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("active", "Saved"),
                            ("returned", "Returned"),
                            ("consumed", "Used"),
                        ],
                        default="active",
                        max_length=16,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                (
                    "goal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="contributions",
                        to="economy.savingsgoal",
                    ),
                ),
                (
                    "ledger_entry",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="savings_contribution",
                        to="economy.ledgerentry",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at", "pk"],
                "indexes": [
                    models.Index(
                        fields=["goal", "state"],
                        name="savings_contrib_goal_state_idx",
                    )
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("amount__gt", 0)),
                        name="savings_contribution_positive_amount",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="SavingsGoalEvent",
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
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("created", "Goal created"),
                            ("mode_selected", "Savings mode selected"),
                            ("current_changed", "Current goal changed"),
                            ("transferred", "Points saved to goal"),
                            ("returned", "Points returned from goal"),
                            ("reached", "Goal reached"),
                            ("completed", "Goal completed"),
                            ("closed", "Goal closed"),
                        ],
                        max_length=24,
                    ),
                ),
                ("description", models.CharField(max_length=240)),
                ("amount", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="savings_goal_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "goal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="events",
                        to="economy.savingsgoal",
                    ),
                ),
            ],
            options={"ordering": ["-created_at", "-pk"]},
        ),
        migrations.CreateModel(
            name="GoalCompletionRequest",
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
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("needs_changes", "Needs changes"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                (
                    "decided_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="decided_goal_completion_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "goal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="completion_requests",
                        to="economy.savingsgoal",
                    ),
                ),
            ],
            options={"ordering": ["requested_at", "pk"]},
        ),
        migrations.AddConstraint(
            model_name="savingsgoal",
            constraint=models.UniqueConstraint(
                condition=models.Q(("mode", "available"), ("status", "active")),
                fields=("child",),
                name="one_current_goal_per_child",
            ),
        ),
        migrations.AddConstraint(
            model_name="goalcompletionrequest",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "pending")),
                fields=("goal",),
                name="one_pending_goal_completion_per_goal",
            ),
        ),
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
                    ("savings_transfer", "Saved to goal"),
                    ("savings_return", "Returned from goal"),
                    ("goal_completion", "Goal completion"),
                ],
                max_length=16,
            ),
        ),
        migrations.RunPython(select_safe_current_goals, migrations.RunPython.noop),
    ]
