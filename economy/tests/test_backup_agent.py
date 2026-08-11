import os
import sqlite3
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from scripts import backup_agent


class BackupAgentTests(TestCase):
    @staticmethod
    def mode(path):
        return stat.S_IMODE(path.stat().st_mode)

    def test_placeholder_repository_is_not_exposed_as_a_configured_target(self):
        with TemporaryDirectory() as directory:
            env_path = Path(directory) / "restic.env"
            env_path.write_text(
                "RESTIC_REPOSITORY=REPLACE_WITH_REPOSITORY\n",
                encoding="utf-8",
            )
            with patch.object(backup_agent, "ENV_PATH", env_path):
                status = backup_agent.initial_status()

        self.assertFalse(status["configured"])
        self.assertEqual(status["provider"], "")
        self.assertEqual(status["target"], "")

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

    def test_provider_uses_s3_repository_hostname(self):
        self.assertEqual(
            backup_agent.provider_from_repository(
                "s3:https://s3.eu-test.backblazeb2.com/family/kinkudos"
            ),
            "backblaze_s3",
        )
        self.assertEqual(
            backup_agent.provider_from_repository(
                "s3:https://example.invalid/backblazeb2.com/family/kinkudos"
            ),
            "s3",
        )

    def test_write_config_verifies_repository_and_keeps_secrets_out_of_result(self):
        with TemporaryDirectory() as directory:
            config_dir = Path(directory) / "backup"
            config_dir.mkdir()
            config_dir.chmod(0o755)
            env_path = config_dir / "restic.env"
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
            self.assertEqual(self.mode(config_dir), 0o700)
            run_command.assert_called_once()

    def test_repository_command_retries_temporary_dns_failure(self):
        failed = CompletedProcess(
            [],
            1,
            "",
            "dial tcp: lookup example.test: server misbehaving",
        )
        succeeded = CompletedProcess([], 0, "[]", "")
        with (
            patch.object(
                backup_agent,
                "run_command",
                side_effect=[failed, succeeded],
            ) as run_command,
            patch.object(backup_agent.time, "sleep"),
        ):
            result = backup_agent.run_repository_command(
                ["restic", "snapshots"],
                env={},
            )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(run_command.call_count, 2)

    def test_dns_error_is_replaced_with_actionable_message(self):
        result = CompletedProcess(
            [],
            1,
            "",
            "dial tcp: lookup example.test on 127.0.0.11:53: server misbehaving",
        )

        self.assertEqual(
            backup_agent.repository_error(result),
            "Could not resolve the storage server. Check the S3 endpoint and try again.",
        )

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
            self.assertEqual(self.mode(output), 0o700)
            self.assertEqual(self.mode(created), 0o600)
            self.assertFalse(expired.exists())

    def test_database_backup_repairs_existing_loose_kinkudos_copy_only(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "kinkudos.sqlite3"
            output = root / "backups"
            output.mkdir()
            output.chmod(0o755)
            with sqlite3.connect(database) as connection:
                connection.execute("CREATE TABLE sample (value TEXT)")

            existing = output / "kinkudos-20990101-000000.sqlite3"
            existing.touch()
            existing.chmod(0o644)
            unrelated = output / "unrelated.sqlite3"
            unrelated.touch()
            unrelated.chmod(0o644)

            with (
                patch.object(backup_agent, "DATABASE_PATH", database),
                patch.object(backup_agent, "OUTPUT_DIR", output),
            ):
                backup_agent.create_database_backup()

            self.assertEqual(self.mode(output), 0o700)
            self.assertEqual(self.mode(existing), 0o600)
            self.assertEqual(self.mode(unrelated), 0o644)

    def test_status_directory_and_atomic_status_file_are_private(self):
        with TemporaryDirectory() as directory:
            state_dir = Path(directory) / "backup-state"
            state_dir.mkdir()
            state_dir.chmod(0o755)
            status_path = state_dir / "status.json"
            status_path.write_text('{"old": true}\n', encoding="utf-8")
            status_path.chmod(0o644)

            with (
                patch.object(backup_agent, "STATE_PATH", status_path),
                patch.object(backup_agent, "STATUS", {"health": "ready"}),
            ):
                backup_agent.save_status()

            self.assertEqual(self.mode(state_dir), 0o700)
            self.assertEqual(self.mode(status_path), 0o600)
            self.assertIn('"health": "ready"', status_path.read_text(encoding="utf-8"))

    def test_database_source_is_opened_query_only(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "kinkudos.sqlite3"
            output = root / "backups"
            output.mkdir()
            with sqlite3.connect(database) as connection:
                connection.execute("CREATE TABLE sample (value TEXT)")
            real_connect = sqlite3.connect
            connections = []

            def recorded_connect(database_path, *args, **kwargs):
                connections.append((database_path, kwargs.copy()))
                return real_connect(database_path, *args, **kwargs)

            with (
                patch.object(backup_agent, "DATABASE_PATH", database),
                patch.object(backup_agent, "OUTPUT_DIR", output),
                patch.object(
                    backup_agent.sqlite3,
                    "connect",
                    side_effect=recorded_connect,
                ),
            ):
                backup_agent.create_database_backup()

            self.assertEqual(
                connections[0],
                (f"{database.resolve().as_uri()}?mode=ro", {"uri": True}),
            )
            with sqlite3.connect(
                f"{database.resolve().as_uri()}?mode=ro",
                uri=True,
            ) as source:
                source.execute("PRAGMA query_only = ON")
                self.assertEqual(source.execute("PRAGMA query_only").fetchone()[0], 1)
                with self.assertRaises(sqlite3.OperationalError):
                    source.execute("INSERT INTO sample VALUES ('blocked')")

    def test_failed_scheduled_backup_keeps_date_unmarked_and_sets_backoff(self):
        status = backup_agent.initial_status()
        status["configured"] = True
        now = datetime.now().astimezone()
        with (
            patch.object(backup_agent, "STATUS", status),
            patch.object(backup_agent, "save_status"),
            patch.object(
                backup_agent,
                "create_database_backup",
                side_effect=RuntimeError("storage unavailable"),
            ),
        ):
            backup_agent.perform_backup(scheduled=True)
            self.assertFalse(backup_agent.scheduled_retry_is_due(now))

        self.assertIsNone(status["last_scheduled_date"])
        self.assertEqual(status["scheduled_retry_attempts"], 1)
        retry_at = datetime.fromisoformat(status["scheduled_retry_not_before"])
        self.assertGreaterEqual(
            retry_at,
            now + timedelta(seconds=backup_agent.SCHEDULED_RETRY_BASE_SECONDS - 1),
        )

    def test_scheduled_backup_retries_after_backoff_and_marks_success(self):
        status = backup_agent.initial_status()
        status["configured"] = True
        status["scheduled_retry_date"] = datetime.now().astimezone().date().isoformat()
        status["scheduled_retry_attempts"] = 1
        status["scheduled_retry_not_before"] = (
            datetime.now().astimezone() - timedelta(minutes=1)
        ).isoformat()
        status["scheduled_retry_deadline"] = (
            datetime.now().astimezone() + timedelta(hours=1)
        ).isoformat()
        successful_command = CompletedProcess([], 0, "", "")
        with (
            patch.object(backup_agent, "STATUS", status),
            patch.object(backup_agent, "save_status"),
            patch.object(backup_agent, "create_database_backup", return_value=Path("/tmp/backup")),
            patch.object(
                backup_agent,
                "restic_environment",
                return_value={"RESTIC_REPOSITORY": "s3:https://example.test/family"},
            ),
            patch.object(
                backup_agent,
                "run_command",
                side_effect=[successful_command, successful_command, successful_command],
            ),
        ):
            backup_agent.perform_backup(scheduled=True)

        today = datetime.now().astimezone().date().isoformat()
        self.assertEqual(status["last_scheduled_date"], today)
        self.assertIsNone(status["scheduled_retry_not_before"])
        self.assertEqual(status["health"], "healthy")
