from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("economy", "0006_penaltytemplate_is_deleted_reward_is_deleted_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="familysettings",
            name="app_name",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AlterField(
            model_name="familysettings",
            name="currency_name",
            field=models.CharField(default="Tokens", max_length=32),
        ),
    ]
