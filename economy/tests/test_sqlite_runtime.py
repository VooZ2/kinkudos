from django.conf import settings
from django.db import connection
from django.test import TestCase


class SqliteRuntimeConfigTests(TestCase):
    def test_sqlite_uses_immediate_transactions_and_aligned_busy_timeout(self):
        self.assertEqual(
            settings.DATABASES["default"]["OPTIONS"].get("transaction_mode"),
            "IMMEDIATE",
        )
        self.assertEqual(settings.DATABASES["default"]["OPTIONS"].get("timeout"), 20)
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA busy_timeout")
            self.assertEqual(cursor.fetchone()[0], 20000)
