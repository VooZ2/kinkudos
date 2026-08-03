from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


def mark_existing_installations_complete(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    FamilySettings = apps.get_model("economy", "FamilySettings")
    if not User.objects.exists():
        return
    family, _created = FamilySettings.objects.get_or_create(pk=1)
    if family.setup_completed_at is None:
        family.setup_completed_at = timezone.now()
        family.save(update_fields=["setup_completed_at"])


class Migration(migrations.Migration):
    dependencies = [("economy", "0022_security_controls")]

    operations = [
        migrations.AddField(
            model_name="familysettings",
            name="setup_completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="familysettings",
            name="default_language",
            field=models.CharField(blank=True, default="", max_length=8),
        ),
        migrations.AddField(
            model_name="familysettings",
            name="timezone_name",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.RunPython(mark_existing_installations_complete, migrations.RunPython.noop),
    ]
