import datetime

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def _default_preset_run_at():
    return datetime.time(7, 0)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("economy", "0032_assignedtaskbatch_nudge_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssignmentPreset",
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
                ("name", models.CharField(max_length=80)),
                ("blocks_rewards", models.BooleanField(default=False)),
                ("is_paused", models.BooleanField(default=False)),
                (
                    "cadence",
                    models.CharField(
                        choices=[
                            ("daily", "Every day"),
                            ("weekdays", "Chosen weekdays"),
                            ("weekend", "Weekend"),
                            ("weekly", "Once a week"),
                        ],
                        default="daily",
                        max_length=16,
                    ),
                ),
                ("weekday_mask", models.PositiveSmallIntegerField(default=0)),
                (
                    "weekend_mode",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("sat", "Saturday"),
                            ("sun", "Sunday"),
                            ("both", "Saturday and Sunday"),
                        ],
                        default="both",
                        max_length=8,
                    ),
                ),
                ("weekly_weekday", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("run_at", models.TimeField(default=_default_preset_run_at)),
                ("last_auto_assigned_on", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "child",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignment_presets",
                        to="economy.childprofile",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="assignment_presets",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["name", "pk"],
            },
        ),
        migrations.CreateModel(
            name="AssignmentPresetItem",
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
                ("custom_title", models.CharField(blank=True, default="", max_length=120)),
                ("custom_points", models.PositiveIntegerField(blank=True, null=True)),
                ("note", models.CharField(blank=True, default="", max_length=200)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                (
                    "preset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="economy.assignmentpreset",
                    ),
                ),
                (
                    "task",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="assignment_preset_items",
                        to="economy.task",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order", "pk"],
            },
        ),
    ]
