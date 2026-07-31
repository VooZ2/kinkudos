import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


def remove_unbound_child_push_subscriptions(apps, schema_editor):
    PushSubscription = apps.get_model("economy", "PushSubscription")
    PushSubscription.objects.filter(child__isnull=False).delete()


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("economy", "0020_lottery_settings"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeviceToken",
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
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("label", models.CharField(blank=True, max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="paired_devices",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at", "-pk"]},
        ),
        migrations.CreateModel(
            name="DevicePairingLink",
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
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="device_pairing_links",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at", "-pk"]},
        ),
        migrations.AddField(
            model_name="pushsubscription",
            name="device",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="push_subscriptions",
                to="economy.devicetoken",
            ),
        ),
        migrations.RunPython(
            remove_unbound_child_push_subscriptions,
            migrations.RunPython.noop,
        ),
        migrations.RemoveConstraint(
            model_name="pushsubscription",
            name="push_subscription_has_one_owner",
        ),
        migrations.AddConstraint(
            model_name="pushsubscription",
            constraint=models.CheckConstraint(
                condition=(
                    Q(child__isnull=True, device__isnull=True, user__isnull=False)
                    | Q(child__isnull=False, device__isnull=False, user__isnull=True)
                ),
                name="push_subscription_has_one_owner",
            ),
        ),
    ]
