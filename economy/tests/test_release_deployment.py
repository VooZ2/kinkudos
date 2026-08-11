import hashlib
import os
import stat
import subprocess
import sys
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]


class ReleaseDeploymentTests(SimpleTestCase):
    def test_base_compose_is_proxy_neutral_and_does_not_publish_gunicorn(self):
        compose = (ROOT / "deploy" / "compose.yml").read_text(encoding="utf-8")

        app_service = compose.split("  backup-agent:", 1)[0]
        self.assertIn("      - backup", app_service)
        self.assertNotIn("traefik.", app_service)
        self.assertNotIn("ports:", app_service)
        self.assertIn(
            "image: ${KINKUDOS_IMAGE_REPOSITORY:-vooz2/kinkudos}:${KINKUDOS_IMAGE_TAG:-26.6.6}",
            app_service,
        )
        self.assertIn("      - app-egress", app_service)

    def test_proxy_overlays_keep_direct_port_private(self):
        host = (ROOT / "deploy" / "compose.host-proxy.yml").read_text(
            encoding="utf-8"
        )
        container = (ROOT / "deploy" / "compose.container-proxy.yml").read_text(
            encoding="utf-8"
        )
        traefik = (ROOT / "deploy" / "compose.traefik.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("127.0.0.1:${KINKUDOS_HTTP_PORT:-8000}:8000", host)
        self.assertIn('name: "${KINKUDOS_PROXY_NETWORK:-proxy}"', container)
        self.assertIn("traefik.http.routers.kinkudos-https.tls", traefik)
        self.assertNotIn("ipallowlist", traefik.lower())

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
        self.assertIn("  app-egress:", networks)
        self.assertNotIn("      - app-egress", backup_service)

    def test_failed_upgrade_does_not_silently_restore_an_old_image(self):
        installer = (ROOT / "deploy" / "install-release.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("database may contain migrations", installer)
        self.assertIn("previous image was not restored automatically", installer)
        self.assertNotIn('docker tag "$old_image_id" "$image"', installer)
        self.assertNotIn("old_image_id=", installer)

    def test_failed_health_check_exits_without_runtime_image_restore(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            (source / "deploy").mkdir(parents=True)
            (source / "scripts").mkdir()
            (source / "pyproject.toml").write_text(
                'version = "26.6.4"\n',
                encoding="utf-8",
            )
            (source / "scripts" / "verify_release.py").write_text(
                "print('verified')\n",
                encoding="utf-8",
            )
            (source / "deploy" / "compose.yml").write_text(
                "services:\n  app:\n    image: vooz2/kinkudos:26.6.4\n",
                encoding="utf-8",
            )
            (source / "deploy" / "compose.traefik.yml").write_text(
                "services: {}\n",
                encoding="utf-8",
            )
            ownership = source / "deploy" / "check-ownership.sh"
            ownership.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            ownership.chmod(0o755)

            archive = root / "release.tar.gz"
            with tarfile.open(archive, "w:gz") as bundle:
                bundle.add(source, arcname="release")
            checksum = root / "release.tar.gz.sha256"
            checksum.write_text(
                f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  release.tar.gz\n",
                encoding="utf-8",
            )

            fake_bin = root / "bin"
            fake_bin.mkdir()
            docker_log = root / "docker.log"
            fake_docker = fake_bin / "docker"
            fake_docker.write_text(
                "#!/bin/sh\n"
                'printf "%s\\n" "$*" >> "$DOCKER_LOG"\n'
                'if [ "$1" = "inspect" ]; then printf "unhealthy\\n"; fi\n'
                'if [ "$1" = "compose" ] && [ "$2" = "config" ] && [ "$3" = "--images" ]; then printf "vooz2/kinkudos:26.6.4\\n"; fi\n'
                "exit 0\n",
                encoding="utf-8",
            )
            fake_docker.chmod(0o755)
            fake_sleep = fake_bin / "sleep"
            fake_sleep.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake_sleep.chmod(0o755)

            project_root = root / "installation"
            (project_root / "deploy").mkdir(parents=True)
            (project_root / "deploy" / "compose.yml").write_text(
                "services:\n  app:\n    image: vooz2/kinkudos:26.6.4\n",
                encoding="utf-8",
            )
            environment = os.environ.copy()
            environment["PATH"] = f"{fake_bin}:{environment['PATH']}"
            environment["DOCKER_LOG"] = str(docker_log)
            result = subprocess.run(
                [
                    "sh",
                    str(ROOT / "deploy" / "install-release.sh"),
                    str(archive),
                    str(checksum),
                    "26.6.4",
                    str(project_root),
                ],
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("database may contain migrations", result.stderr)
            self.assertIn("previous image was not restored automatically", result.stderr)
            self.assertNotIn(" tag ", docker_log.read_text(encoding="utf-8"))

    def test_release_updater_refreshes_versioned_deployment_helpers(self):
        installer = (ROOT / "deploy" / "install-release.sh").read_text(
            encoding="utf-8"
        )
        backup_script = (ROOT / "deploy" / "backup.sh").read_text(encoding="utf-8")

        self.assertIn('"$release_dir/deploy/$helper" "$deploy_dir/$helper"', installer)
        self.assertIn('image_tag=${KINKUDOS_IMAGE_TAG:-$version}', installer)
        self.assertIn('export KINKUDOS_IMAGE_TAG="$image_tag"', installer)
        self.assertIn('image_repository=${KINKUDOS_IMAGE_REPOSITORY:-vooz2/kinkudos}', installer)
        self.assertIn('export KINKUDOS_IMAGE_REPOSITORY="$image_repository"', installer)
        self.assertIn('image="$image_repository:$image_tag"', installer)
        self.assertIn("  backup.sh \\", installer)
        self.assertIn("  install.sh \\", installer)
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
            backups = root / "backups"
            backups.mkdir()
            backups.chmod(0o755)
            backup_state = root / "backup-state"
            backup_state.mkdir()
            backup_state.chmod(0o755)
            existing_backup = backups / "kinkudos-20990101-000000.sqlite3"
            existing_backup.touch()
            existing_backup.chmod(0o644)
            unrelated_backup = backups / "unrelated.sqlite3"
            unrelated_backup.touch()
            unrelated_backup.chmod(0o644)
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
                    "26.6.4",
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
            self.assertEqual(stat.S_IMODE(backups.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(backup_state.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(existing_backup.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(unrelated_backup.stat().st_mode), 0o644)

    def test_public_installer_verifies_release_and_refuses_existing_install(self):
        installer = (ROOT / "deploy" / "install.sh").read_text(encoding="utf-8")

        self.assertIn("sha256sum -c", installer)
        self.assertIn("Unsafe archive member", installer)
        self.assertIn("releases/latest", installer)
        self.assertIn('KINKUDOS_INSTALL_ROOT:-/opt/kinkudos', installer)
        self.assertIn("KINKUDOS_RELEASE_BASE_URL", installer)
        self.assertIn("KINKUDOS_IMAGE_TAG", installer)
        self.assertIn("is not empty; use the upgrade guide", installer)
        self.assertIn("./bootstrap.sh", installer)
        self.assertIn("is not writable by the current user", installer)
        self.assertNotIn("sudo sh", installer)

    def test_public_installer_leaves_nonempty_installation_untouched(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            install_root = root / "existing"
            install_root.mkdir()
            sentinel = install_root / "family-data"
            sentinel.write_text("keep", encoding="utf-8")

            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_docker = fake_bin / "docker"
            fake_docker.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake_docker.chmod(fake_docker.stat().st_mode | stat.S_IXUSR)

            environment = os.environ.copy()
            environment["PATH"] = f"{fake_bin}:{environment['PATH']}"
            environment["KINKUDOS_VERSION"] = "26.6.4"
            environment["KINKUDOS_INSTALL_ROOT"] = str(install_root)
            result = subprocess.run(
                ["sh", str(ROOT / "deploy" / "install.sh")],
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("is not empty", result.stderr)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_hostinger_catalog_compose_is_self_contained_and_traefik_ready(self):
        compose = (ROOT / "deploy" / "hostinger" / "compose.yaml").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "image: ${KINKUDOS_IMAGE_REPOSITORY:-vooz2/kinkudos}:${KINKUDOS_IMAGE_TAG:-26.6.6}",
            compose,
        )
        self.assertIn("kinkudos-data:/app/data", compose)
        self.assertIn('      - "8000"', compose)
        self.assertIn("KINKUDOS_RUNTIME_SECRETS_DIR", compose)
        self.assertIn("/health/", compose)
        self.assertIn("traefik.enable=true", compose)
        self.assertIn("entrypoints=websecure", compose)
        self.assertIn("tls.certresolver=letsencrypt", compose)
        self.assertIn("loadbalancer.server.port=8000", compose)
        self.assertNotIn("backup-agent", compose)
        self.assertNotIn("restic", compose.lower())
        self.assertNotIn("caddy", compose.lower())
        self.assertNotIn("build:", compose)
        self.assertNotIn("privileged", compose)
        self.assertNotIn("docker.sock", compose)
        self.assertNotIn("network_mode", compose)
        self.assertNotIn("ports:", compose)
        self.assertNotIn("../", compose)

    def test_rc_workflow_uses_dedicated_candidate_repositories(self):
        workflow = (ROOT / ".github" / "workflows" / "release-candidate.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("  workflow_dispatch:\n", workflow)
        self.assertNotIn("\n  push:\n", workflow)
        self.assertNotIn("github.event_name", workflow)
        self.assertIn("ref: ${{ inputs.source_ref }}", workflow)
        self.assertIn("SOURCE_REF: ${{ inputs.source_ref }}", workflow)
        self.assertIn("ghcr.io/vooz2/kinkudos-rc", workflow)
        self.assertIn("vooz2/kinkudos-rc", workflow)
        self.assertNotIn("ghcr.io/vooz2/kinkudos\n", workflow)
        self.assertNotIn("vooz2/kinkudos\n", workflow)

        workflow = (ROOT / ".github" / "workflows" / "release-image.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "docker compose -f deploy/hostinger/compose.yaml config --quiet", workflow
        )

    def test_release_workflow_runs_locked_production_deploy_checks(self):
        workflow = (ROOT / ".github" / "workflows" / "release-image.yml").read_text(
            encoding="utf-8"
        )
        validator = (ROOT / "scripts" / "check_deploy.py").read_text(encoding="utf-8")

        self.assertIn('python-version: "3.12"', workflow)
        self.assertIn("python -m pip install --disable-pip-version-check --requirement requirements.lock", workflow)
        self.assertIn("python manage.py check", workflow)
        self.assertIn("python scripts/check_deploy.py", workflow)
        self.assertEqual(workflow.count("python scripts/check_deploy.py"), 1)
        self.assertIn('"--deploy"', validator)
        for setting in (
            "KINKUDOS_DEBUG: \"false\"",
            "KINKUDOS_SECRET_KEY: ci-deploy-check-only-",
            "KINKUDOS_ALLOWED_HOSTS: test.example.com",
            "KINKUDOS_CSRF_TRUSTED_ORIGINS: https://test.example.com",
            "KINKUDOS_SECURE_COOKIES: \"true\"",
            "KINKUDOS_SECURE_SSL_REDIRECT: \"true\"",
            "KINKUDOS_HSTS_SECONDS: \"31536000\"",
        ):
            self.assertIn(setting, workflow)
        self.assertIn("security.W005", validator)
        self.assertIn("security.W021", validator)
        self.assertNotIn("SILENCED_SYSTEM_CHECKS", workflow + validator)
        for script_name in ("bootstrap.sh", "install-release.sh"):
            script = (ROOT / "deploy" / script_name).read_text(encoding="utf-8")
            self.assertIn("chmod 0700", script)
            self.assertIn('"$project_root/backups"/kinkudos-*.sqlite3', script)

    def test_dependency_security_monitoring_is_configured(self):
        dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn('package-ecosystem: "pip"', dependabot)
        self.assertIn('package-ecosystem: "github-actions"', dependabot)
        self.assertIn(
            "pypa/gh-action-pip-audit@1220774d901786e6f652ae159f7b6bc8fea6d266",
            workflow,
        )
        self.assertIn("inputs: requirements.lock", workflow)
        self.assertIn("no-deps: true", workflow)
        migration_check = workflow.split(
            "      - name: Check for missing migrations\n", 1
        )[1].split("      - name:", 1)[0]
        self.assertIn('KINKUDOS_DEBUG: "false"', migration_check)
        self.assertIn("KINKUDOS_SECRET_KEY: ci-test-only-", migration_check)

    def test_legacy_hostinger_caddy_profile_is_removed(self):
        legacy_paths = (
            "Caddyfile.hostinger",
            "compose.hostinger.yml",
            "hostinger-bootstrap.sh",
            "hostinger-healthcheck.sh",
            "install-hostinger.sh",
            "uninstall-hostinger.sh",
        )
        for relative in legacy_paths:
            self.assertFalse((ROOT / "deploy" / relative).exists(), relative)

        updater = (ROOT / "deploy" / "install-release.sh").read_text(
            encoding="utf-8"
        )
        packager = (ROOT / "scripts" / "package_release.py").read_text(
            encoding="utf-8"
        )
        verifier = (ROOT / "scripts" / "verify_release.py").read_text(
            encoding="utf-8"
        )
        for legacy_reference in legacy_paths:
            self.assertNotIn(legacy_reference, updater)
            self.assertNotIn(legacy_reference, packager)
            self.assertNotIn(legacy_reference, verifier)
        self.assertNotIn("hostinger-caddy-v1", updater)

    def test_release_updater_rejects_removed_installation_profiles(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            deploy = root / "deploy"
            deploy.mkdir()
            (deploy / "compose.yml").write_text(
                "services: {}\n", encoding="utf-8"
            )
            (root / "install-profile").write_text(
                "hostinger-caddy-v1\n", encoding="utf-8"
            )
            archive = root / "release.tar.gz"
            archive.write_bytes(b"not a release")
            checksum = root / "release.tar.gz.sha256"
            checksum.write_text(
                f"{'0' * 64}  release.tar.gz\n", encoding="utf-8"
            )

            result = subprocess.run(
                [
                    "sh",
                    str(ROOT / "deploy" / "install-release.sh"),
                    str(archive),
                    str(checksum),
                    "26.6.4",
                    str(root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "Unsupported installation profile: hostinger-caddy-v1",
                result.stderr,
            )
            self.assertFalse((root / "secrets").exists())

    def test_entrypoint_persists_hostinger_runtime_secrets(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            runtime_secrets = root / "runtime-secrets"
            environment = os.environ.copy()
            environment.update(
                {
                    "PATH": f"{Path(sys.executable).parent}:{environment['PATH']}",
                    "KINKUDOS_DEBUG": "true",
                    "KINKUDOS_DATABASE_PATH": str(root / "kinkudos.sqlite3"),
                    "KINKUDOS_MEDIA_ROOT": str(root / "media"),
                    "KINKUDOS_RUNTIME_SECRETS_DIR": str(runtime_secrets),
                    "KINKUDOS_SECRET_KEY_FILE": str(runtime_secrets / "django_secret_key"),
                    "KINKUDOS_VAPID_PRIVATE_KEY_FILE": str(
                        runtime_secrets / "vapid_private.pem"
                    ),
                    "KINKUDOS_VAPID_PUBLIC_KEY_FILE": str(
                        runtime_secrets / "vapid_public.txt"
                    ),
                    "KINKUDOS_SETUP_TOKEN": "test-setup-token",
                }
            )

            command = ["sh", str(ROOT / "docker" / "entrypoint.sh"), "true"]
            first = subprocess.run(command, env=environment, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            secret_files = [
                runtime_secrets / "django_secret_key",
                runtime_secrets / "vapid_private.pem",
                runtime_secrets / "vapid_public.txt",
            ]
            self.assertTrue(all(path.is_file() and path.stat().st_size for path in secret_files))
            initial_hashes = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in secret_files
            }

            second = subprocess.run(command, env=environment, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(
                initial_hashes,
                {
                    path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in secret_files
                },
            )
