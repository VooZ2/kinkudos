import os
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from scripts import backup_agent


class BackupAgentTests(TestCase):
    def test_provider_and_public_target_do_not_expose_embedded_credentials(self):
        repository = "s3:https://secret@example.invalid/family/kinkudos"

        self.assertEqual(
            backup_agent.provider_from_repository(repository),
            "s3",
        )
        self.assertEqual(
            backup_agent.public_target(repository),
            "example.invalid/family/kinkudos",
        )

    def test_write_config_verifies_repository_and_keeps_secrets_out_of_result(self):
        with TemporaryDirectory() as directory:
            env_path = Path(directory) / "restic.env"
            with (
                patch.object(backup_agent, "ENV_PATH", env_path),
                patch.object(
                    backup_agent,
                    "run_command",
                    return_value=CompletedProcess([], 0, "[]", ""),
                ) as run_command,
            ):
                repository, key_hint = backup_agent.write_config(
                    {
                        "provider": "backblaze_s3",
                        "endpoint": "s3.eu-test.backblazeb2.com",
                        "bucket": "family",
                        "region": "eu-test",
                        "access_key_id": "access-key-1234",
                        "secret_access_key": "never-return-this",
                    }
                )

            self.assertEqual(
                repository,
                "s3:https://s3.eu-test.backblazeb2.com/family/kinkudos",
            )
            self.assertEqual(key_hint, "1234")
            self.assertIn("never-return-this", env_path.read_text(encoding="utf-8"))
            self.assertNotIn("never-return-this", repository)
            run_command.assert_called_once()

    def test_database_backup_is_consistent_and_removes_expired_local_copy(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "kinkudos.sqlite3"
            output = root / "backups"
            output.mkdir()
            with sqlite3.connect(database) as connection:
                connection.execute("CREATE TABLE sample (value TEXT)")
                connection.execute("INSERT INTO sample VALUES ('kept')")
            expired = output / "kinkudos-20000101-000000.sqlite3"
            expired.touch()
            old_timestamp = (datetime.now(UTC) - timedelta(days=32)).timestamp()
            expired.chmod(0o600)
            expired.touch()
            os.utime(expired, (old_timestamp, old_timestamp))

            with (
                patch.object(backup_agent, "DATABASE_PATH", database),
                patch.object(backup_agent, "OUTPUT_DIR", output),
            ):
                created = backup_agent.create_database_backup()

            with sqlite3.connect(created) as connection:
                value = connection.execute("SELECT value FROM sample").fetchone()[0]
            self.assertEqual(value, "kept")
            self.assertFalse(expired.exists())
