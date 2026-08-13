from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("economy", "0034_alter_assignmentpreset_run_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="taskclaim",
            name="child_note",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
    ]
