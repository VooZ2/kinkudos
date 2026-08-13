import economy.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("economy", "0033_assignment_presets"),
    ]

    operations = [
        migrations.AlterField(
            model_name="assignmentpreset",
            name="run_at",
            field=models.TimeField(default=economy.models._default_preset_run_at),
        ),
    ]
