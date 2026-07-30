import os
import stat
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]


class ReleaseDeploymentTests(SimpleTestCase):
    def test_compose_pins_traefik_to_public_web_network(self):
        compose = (ROOT / "deploy" / "compose.yml").read_text(encoding="utf-8")

        self.assertIn("traefik.docker.network: web", compose)
        app_service = compose.split("  backup-agent:", 1)[0]
        self.assertIn("      - web", app_service)
        self.assertIn("      - backup", app_service)

    def test_backup_agent_has_isolated_app_network_and_outbound_network(self):
        compose = (ROOT / "deploy" / "compose.yml").read_text(encoding="utf-8")
        backup_service = compose.split("  backup-agent:", 1)[1].split(
            "\nnetworks:", 1
        )[0]
        networks = compose.split("\nnetworks:", 1)[1]

        self.assertIn("      - backup", backup_service)
        self.assertIn("      - backup-egress", backup_service)
        self.assertIn("      - ../data:/source", backup_service)
        self.assertNotIn("../data:/source:ro", backup_service)
        self.assertIn("  backup:\n    internal: true", networks)
        self.assertIn("  backup-egress:", networks)

    def test_release_updater_refreshes_versioned_deployment_helpers(self):
        installer = (ROOT / "deploy" / "install-release.sh").read_text(
            encoding="utf-8"
        )
        backup_script = (ROOT / "deploy" / "backup.sh").read_text(encoding="utf-8")

        self.assertIn('"$release_dir/deploy/$helper" "$deploy_dir/$helper"', installer)
        self.assertIn("  backup.sh \\", installer)
        self.assertIn("  kinkudos-lottery-reminders.service \\", installer)
        self.assertIn("  kinkudos-lottery-reminders.timer \\", installer)
        self.assertNotIn("docker compose run --rm restic", backup_script)
        self.assertIn("python manage.py run_backup", backup_script)

    def test_updater_uses_runtime_uid_and_gid_for_backup_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            deploy = root / "deploy"
            deploy.mkdir()
            (deploy / "compose.yml").write_text("services: {}\n", encoding="utf-8")
            (deploy / ".env").write_text(
                "KINKUDOS_UID=4242\nKINKUDOS_GID=4343\n",
                encoding="utf-8",
            )
            archive = root / "release.tar.gz"
            archive.write_bytes(b"not a release")
            checksum = root / "release.tar.gz.sha256"
            checksum.write_text(f"{'0' * 64}  release.tar.gz\n", encoding="utf-8")

            fake_bin = root / "bin"
            fake_bin.mkdir()
            chown_log = root / "chown.log"
            fake_chown = fake_bin / "chown"
            fake_chown.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$*" >> "$CHOWN_LOG"\n',
                encoding="utf-8",
            )
            fake_chown.chmod(fake_chown.stat().st_mode | stat.S_IXUSR)
            environment = os.environ.copy()
            environment["PATH"] = f"{fake_bin}:{environment['PATH']}"
            environment["CHOWN_LOG"] = str(chown_log)

            result = subprocess.run(
                [
                    "sh",
                    str(ROOT / "deploy" / "install-release.sh"),
                    str(archive),
                    str(checksum),
                    "26.3.1",
                    str(root),
                ],
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("Release checksum does not match.", result.stderr)
            ownership = chown_log.read_text(encoding="utf-8")
            self.assertIn("4242:4343", ownership)
            self.assertIn(str(root / "backups"), ownership)
            self.assertIn(str(root / "backup-state"), ownership)
            self.assertIn(str(root / "secrets" / "backup" / "restic.env"), ownership)
            self.assertIn(str(root / "secrets" / "smtp"), ownership)
