from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("economy", "0013_birth_date_change_requests"),
    ]

    operations = [
        migrations.AddField(
            model_name="taskclaim",
            name="child_acknowledged_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
