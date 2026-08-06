from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("economy", "0024_savings_goal_modes")]

    operations = [
        migrations.AddField(
            model_name="proposal",
            name="goal_mode",
            field=models.CharField(
                blank=True,
                choices=[("available", "Current goal"), ("saved", "Saved")],
                max_length=16,
                null=True,
            ),
        ),
    ]
