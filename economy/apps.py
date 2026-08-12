from django.apps import AppConfig
from django.core.signals import request_finished, request_started
from django.db.backends.signals import connection_created


def configure_sqlite(sender, connection, **kwargs):
    if connection.vendor != "sqlite":
        return
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = ON")
        # Keep busy_timeout aligned with DATABASES OPTIONS timeout (seconds → ms).
        cursor.execute("PRAGMA busy_timeout = 20000")
        if connection.settings_dict["NAME"] != ":memory:":
            cursor.execute("PRAGMA journal_mode = WAL")


def activate_family_settings_cache(**kwargs):
    from economy.models import FamilySettings

    FamilySettings.activate_load_cache()


def deactivate_family_settings_cache(**kwargs):
    from economy.models import FamilySettings

    FamilySettings.deactivate_load_cache()


class EconomyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "economy"

    def ready(self):
        connection_created.connect(
            configure_sqlite,
            dispatch_uid="economy.configure_sqlite",
        )
        request_started.connect(
            activate_family_settings_cache,
            dispatch_uid="economy.activate_family_settings_cache",
        )
        request_finished.connect(
            deactivate_family_settings_cache,
            dispatch_uid="economy.deactivate_family_settings_cache",
        )

