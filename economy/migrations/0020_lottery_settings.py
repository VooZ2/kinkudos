from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [  # noqa: RUF012
        ("economy", "0019_lottery"),
    ]

    operations = [  # noqa: RUF012
        migrations.AddField(
            model_name="familysettings",
            name="lottery_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="familysettings",
            name="lottery_ticket_cost",
            field=models.PositiveSmallIntegerField(
                default=15,
                validators=[MinValueValidator(1), MaxValueValidator(10000)],
            ),
        ),
        migrations.AddField(
            model_name="familysettings",
            name="lottery_weekly_limit",
            field=models.PositiveSmallIntegerField(
                default=3,
                validators=[MinValueValidator(1), MaxValueValidator(100)],
            ),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="lottery_enabled",
            field=models.BooleanField(default=True),
        ),
    ]
