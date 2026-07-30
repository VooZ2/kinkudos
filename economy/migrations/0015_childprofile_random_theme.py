from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("economy", "0014_taskclaim_child_acknowledged_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="childprofile",
            name="randomize_theme_daily",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="theme_randomized_on",
            field=models.DateField(blank=True, null=True),
        ),
    ]
