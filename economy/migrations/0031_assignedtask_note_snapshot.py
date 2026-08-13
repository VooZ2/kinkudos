from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("economy", "0030_alter_ledgerentry_kind"),
    ]

    operations = [
        migrations.AddField(
            model_name="assignedtask",
            name="note_snapshot",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
    ]
