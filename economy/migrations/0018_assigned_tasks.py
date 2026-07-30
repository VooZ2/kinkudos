from typing import ClassVar

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies: ClassVar = [
        ("economy", "0017_rename_blockville_theme"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations: ClassVar = [
        migrations.CreateModel(
            name="AssignedTaskBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("blocks_rewards", models.BooleanField(default=False)),
                ("assigned_on", models.DateField(default=django.utils.timezone.localdate)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("assigned_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="assigned_task_batches", to=settings.AUTH_USER_MODEL)),
                ("child", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="assigned_task_batches", to="economy.childprofile")),
            ],
            options={"ordering": ["-created_at", "-pk"]},
        ),
        migrations.CreateModel(
            name="TaskCompletion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("completed_on", models.DateField(default=django.utils.timezone.localdate)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("child", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="task_completions", to="economy.childprofile")),
                ("task", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="completions", to="economy.task")),
            ],
            options={
                "ordering": ["-created_at", "-pk"],
                "indexes": [models.Index(fields=["child", "task", "completed_on"], name="task_done_child_day_idx")],
            },
        ),
        migrations.AlterField(
            model_name="ledgerentry",
            name="kind",
            field=models.CharField(choices=[("task", "Task"), ("assigned_task", "Assigned task"), ("penalty", "Penalty"), ("reward", "Reward"), ("adjustment", "Adjustment"), ("gift", "Gift"), ("birthday", "Birthday")], max_length=16),
        ),
        migrations.CreateModel(
            name="AssignedTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title_snapshot", models.CharField(max_length=120)),
                ("icon_snapshot", models.CharField(default="🧹", max_length=32)),
                ("reward_snapshot", models.PositiveIntegerField()),
                ("status", models.CharField(choices=[("pending", "Pending"), ("completed", "Completed"), ("cancelled", "Cancelled")], default="pending", max_length=16)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("cancelled_at", models.DateTimeField(blank=True, null=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="items", to="economy.assignedtaskbatch")),
                ("cancelled_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="cancelled_assigned_tasks", to=settings.AUTH_USER_MODEL)),
                ("ledger_entry", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="assigned_task", to="economy.ledgerentry")),
                ("task", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="assignments", to="economy.task")),
            ],
            options={"ordering": ["pk"]},
        ),
    ]
