from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("economy", "0026_devicetoken_device_browser_devicetoken_device_code_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pushsubscription",
            name="endpoint",
            field=models.CharField(max_length=2048, unique=True),
        ),
        migrations.AlterField(
            model_name="pushsubscription",
            name="p256dh",
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name="pushsubscription",
            name="auth",
            field=models.CharField(max_length=128),
        ),
    ]
