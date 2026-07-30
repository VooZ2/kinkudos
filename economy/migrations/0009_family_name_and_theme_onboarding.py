from django.db import migrations, models


def keep_existing_profiles_and_extract_family_name(apps, schema_editor):
    ChildProfile = apps.get_model("economy", "ChildProfile")
    FamilySettings = apps.get_model("economy", "FamilySettings")

    ChildProfile.objects.update(theme_selected=True)
    for family in FamilySettings.objects.all():
        name = family.family_name.strip()
        for suffix in (" Family", " Šeima"):
            if name.endswith(suffix):
                name = name[: -len(suffix)].strip()
                break
        family.family_name = name
        family.save(update_fields=["family_name"])


class Migration(migrations.Migration):
    dependencies = [
        ("economy", "0008_translate_model_labels"),
    ]

    operations = [
        migrations.RenameField(
            model_name="familysettings",
            old_name="app_name",
            new_name="family_name",
        ),
        migrations.AlterField(
            model_name="familysettings",
            name="family_name",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="theme_selected",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(
            keep_existing_profiles_and_extract_family_name,
            migrations.RunPython.noop,
        ),
    ]
