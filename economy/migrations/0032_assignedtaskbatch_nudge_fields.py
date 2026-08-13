from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("economy", "0031_assignedtask_note_snapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="assignedtaskbatch",
            name="nudge_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="assignedtaskbatch",
            name="nudge_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
