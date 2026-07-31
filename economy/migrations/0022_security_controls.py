import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("economy", "0021_device_pairing"),
    ]

    operations = [
        migrations.AddField(
            model_name="familysettings",
            name="allowed_networks",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="familysettings",
            name="network_access_mode",
            field=models.CharField(
                choices=[
                    ("open", "Internet access"),
                    ("children", "Restrict child access"),
                    ("all", "Restrict all access"),
                ],
                default="open",
                max_length=16,
            ),
        ),
        migrations.CreateModel(
            name="AttemptCounter",
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
                    "scope",
                    models.CharField(
                        choices=[
                            ("child_pin_device", "Child PIN by device"),
                            ("child_pin_profile", "Child PIN by profile"),
                            ("child_pin_ip", "Child PIN by IP"),
                            ("child_pin_site", "Child PIN site-wide"),
                            ("parent_login_ip", "Parent login by IP"),
                            ("parent_login_account", "Parent login by account"),
                            ("password_reset_ip", "Password reset by IP"),
                            ("password_reset_account", "Password reset by account"),
                            ("device_pairing", "Device pairing"),
                            ("admin_login_ip", "Admin login by IP"),
                        ],
                        max_length=32,
                    ),
                ),
                ("key_hash", models.CharField(max_length=64)),
                ("window_start", models.DateTimeField()),
                ("count", models.PositiveIntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name="SecurityAuditEvent",
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
                    "action",
                    models.CharField(
                        choices=[
                            ("device_paired", "Child device paired"),
                            ("device_revoked", "Child device revoked"),
                            ("all_devices_revoked", "All child devices revoked"),
                            ("network_policy_changed", "Network access changed"),
                        ],
                        max_length=32,
                    ),
                ),
                ("detail", models.CharField(blank=True, max_length=240)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="security_audit_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at", "-pk"]},
        ),
        migrations.AddConstraint(
            model_name="attemptcounter",
            constraint=models.UniqueConstraint(
                fields=("scope", "key_hash", "window_start"),
                name="uniq_attempt_counter_window",
            ),
        ),
        migrations.AddIndex(
            model_name="attemptcounter",
            index=models.Index(
                fields=["scope", "key_hash"],
                name="economy_att_scope_5156ea_idx",
            ),
        ),
    ]
