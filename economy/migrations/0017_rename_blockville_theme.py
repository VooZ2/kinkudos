from typing import ClassVar

from django.db import migrations, models


def rename_theme(apps, schema_editor):
    ChildProfile = apps.get_model("economy", "ChildProfile")
    ChildProfile.objects.filter(theme="robliux").update(theme="blockville")


class Migration(migrations.Migration):
    dependencies: ClassVar = [
        ("economy", "0016_alter_childprofile_theme_backupauditevent"),
    ]

    operations: ClassVar = [
        migrations.RunPython(rename_theme, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="childprofile",
            name="theme",
            field=models.CharField(
                choices=[
                    ("neutral", "Neutral"),
                    ("magic_academy", "Magic Academy"),
                    ("block_world", "Block World"),
                    ("hero_hq", "Superhero HQ"),
                    ("art_studio", "Art Studio"),
                    ("panda_pet", "Panda World"),
                    ("blockville", "Blockville World"),
                ],
                default="neutral",
                max_length=32,
            ),
        ),
    ]
