# Release rules

Every user-visible product change must be included in `CHANGELOG.md` before a
new version is released.

## Version selection

KinKudos uses the `YY.FEATURE.FIX` versioning scheme:

- `YY` is the last two digits of the release year, for example `26` for 2026;
- `FEATURE` increases when genuinely new functionality is added during that
  year;
- `FIX` increases for bug fixes, patches, design changes, and improvements to
  existing functionality.

At the start of a new year, update `YY` and reset the other two numbers to `0`.
Production releases must not include a `BETA` suffix.

Examples:

- the first production release in 2026 is `26.0.0`;
- a bug fix or design correction after `26.0.0` becomes `26.0.1`;
- new functionality after `26.0.1` becomes `26.1.0`;
- the first release in 2027 becomes `27.0.0`.

A documentation-only or development-process change that does not change the
installed application does not require a new product version.

## Git and release workflow

`main` must remain stable. Product development does not happen directly on
`main`; use one short-lived `release/<version>` branch for the upcoming
product release. Do not bump the application version merely by creating the
branch. The version is updated during release preparation.

Validated product releases follow this path:

```text
release/<version>
-> pre-release validation
-> Pull Request to main
-> required KinKudos CI PASS
-> squash merge
-> tag from the validated merged main commit
-> GitHub Release
-> release-image workflow
-> AMD64/ARM64 Docker publication
```

The release tag must be created only from the already merged and validated
`main` commit. The release image workflow expects a tag in the form
`v<version>`, validates the tag and project metadata, and then publishes the
release images.

All product code, tests, release preparation, and related internal changes for
the same release may remain on its `release/<version>` branch. Integrate the
branch through a Pull Request, wait for the required `KinKudos CI` status check
to pass, and squash-merge it into `main` before tagging.

Independent official documentation changes use a `docs/<topic>` branch and are
not product releases. Documentation for functionality that exists only on an
unreleased product branch may use a `docs/<topic>` branch created from that
release branch and merged back into the same release branch. Documentation-only
changes do not require a product version bump, product tag, GitHub Release,
Docker publication, or product changelog entry.

The PR CI workflow intentionally does not require `scripts/verify_release.py`
for every development PR. A release branch may still contain the previous
official version until release preparation. `verify_release.py` remains part
of final release and release-image validation, after the version metadata has
been prepared.

## Release checklist

For each product release:

1. Update the version in `kinkudos/settings.py`, `pyproject.toml`,
   `deploy/compose.yml`, `deploy/hostinger/compose.yaml`, and every other
   deployment file that pins the release image version.
2. Do not automatically edit `README.md` or `README.lt.md`. Their structure,
   design, screenshots, badges, and marketing copy are protected. Change a
   README only when a specific existing hard-coded technical value must be
   updated for that release. `<version>` placeholders and dynamic `latest`
   release badges or links do not by themselves require a README change.
3. Add a dated version heading to `CHANGELOG.md`.
4. Record new functionality under `Added`.
5. Record behaviour changes under `Changed`, bug fixes under `Fixed`, and
   security changes under `Security`.
6. Verify that `/changes/` presents the release content as “What's new?” and
   “What was fixed?”.
7. Run the full test suite and Django checks in Python 3.12 with
   `requirements.lock`. Run the checks with production-like settings:

   ```text
   KINKUDOS_DEBUG=false
   KINKUDOS_SECRET_KEY=<temporary CI-only value>
   KINKUDOS_ALLOWED_HOSTS=test.example.com
   KINKUDOS_CSRF_TRUSTED_ORIGINS=https://test.example.com
   KINKUDOS_SECURE_COOKIES=true
   KINKUDOS_SECURE_SSL_REDIRECT=true
   KINKUDOS_HSTS_SECONDS=31536000
   ```

   At minimum, run `python -m ruff check .`, `python manage.py check`,
   `python scripts/check_deploy.py`,
   `python manage.py makemigrations --check --dry-run`,
   `python -m pip check`, and `python manage.py test`. `check_deploy.py`
   runs `python manage.py check --deploy` and rejects unexpected warnings.
   Do not run the deployment check with ordinary development defaults. The
   deliberate HSTS policy currently permits only `security.W005` and
   `security.W021`; any new warning must stop release validation.
8. Write GitHub Release notes in English and keep the same structure as the
   corresponding `CHANGELOG.md` entry. The release text may be copied directly
   from `CHANGELOG.md`.
9. Create and upload the required custom GitHub Release assets:
   `kinkudos-<version>.tar.gz` and `kinkudos-<version>.tar.gz.sha256`. These are
   separate from GitHub's automatically generated `Source code (zip)` and
   `Source code (tar.gz)` downloads, and the documented installation and
   upgrade flows depend on these named assets. Create the archive from the
   exact validated release commit, with the top-level directory
   `kinkudos-<version>/`; it must contain every public file required by those
   flows, including at minimum
   `kinkudos-<version>/deploy/install-release.sh` and
   `kinkudos-<version>/deploy/compose.yml`. Do not include `.git`, local
   environment files, databases, uploads, backups, secrets, caches, logs, or
   other private runtime state. The checksum file must reference exactly
   `kinkudos-<version>.tar.gz` and pass
   `sha256sum -c kinkudos-<version>.tar.gz.sha256`. Upload both files to the
   GitHub Release and verify that they are remotely downloadable and pass
   checksum and documented archive-extraction checks before considering
   publication complete.
10. After creating the version tag, wait for the container workflow to build and
   publish both AMD64 and ARM64 images to GHCR and Docker Hub. The workflow
   publishes the immutable full version (for example `26.4.7`), the current
   patch series (for example `26.4`), and `latest`. Production deployments must
   always use the full version rather than a floating tag.
11. For deployment or setup changes, additionally validate:
    - a clean Hostinger Ubuntu 24.04 Docker-profile installation on an empty
      VPS;
    - a clean installation with the general guided installer;
    - a clean Docker Compose installation;
    - the first Web UI setup and protection of its setup code;
    - both skipping SMTP and configuring SMTP;
    - that setup is no longer available after it is completed;
    - upgrading a real previous instance while preserving its data;
    - CLI password recovery and the emergency administrator;
    - creating a backup and performing an isolated restore test;
    - Hostinger HTTP-to-HTTPS redirect, certificate issuance, health check, and
      safe container removal without deleting data or certificates.
12. For documentation changes, run a strict MkDocs build and validate internal
    and external links, old-URL redirects, canonical URLs, `hreflang`, the
    sitemap, `robots.txt`, and that every sitemap URL returns `200` directly.

Documentation changes to `docs.kinkudos.app`, the README, or other
documentation do not belong in the product changelog and do not change the
product version.

## Migration and rollback contract

The application image runs Django migrations before starting Gunicorn. Release
migrations must therefore follow an expand/contract policy: add nullable or
defaulted schema first, deploy code that can read both representations, migrate
existing data, and remove old representations only in a later release after
all supported images have moved forward.

`deploy/install-release.sh` creates a database backup before replacing the
running containers and health-checks the new image. If the new image fails its
health check, the updater fails loudly and does not retag or restart the old
image: migrations may already have changed the live database, and silently
starting an older image could leave it incompatible with that schema. Restore
is an explicit, separately verified operator action; the updater never
automatically overwrites newer family data with a pre-upgrade backup.

The version shown in the application header must always remain a link to
`/changes/`.

The repository Actions secret `DOCKERHUB_TOKEN` must contain only the Docker
Hub access-token value, without a username or `username:` prefix. The
publishing Docker ID is `vooz2`.

## Release candidate QA

### RC build — only when VPS / installer acceptance is needed

A release candidate is not required for every release or every commit.

When real VPS, installer, or deployment acceptance testing is needed, a
maintainer manually starts the `Build release candidate` workflow in GitHub
Actions by selecting **Run workflow**. Set `source_ref` to the relevant
`release/<version>` branch or to a full commit SHA that is contained by a
release branch. A normal push to `release/<version>` does not start this
workflow and does not create an RC.

The workflow validates the exact selected source commit, builds
`linux/amd64` and `linux/arm64` images, and publishes only the immutable
candidate tag `<version>-rc.<short-sha>` to the dedicated
`ghcr.io/vooz2/kinkudos-rc` and `vooz2/kinkudos-rc` packages. It also uploads
`kinkudos-<version>.tar.gz` and its checksum to the prerelease
`v<version>-rc.<short-sha>`. It never writes to the production `kinkudos`
packages or updates a stable version tag, a minor-series tag, or `latest`.

These are QA-only artifacts, not production releases. If a release does not
require VPS or deployment acceptance, it may proceed from normal release
validation directly to the separate stable publication process without an RC.

For fresh-install acceptance testing, use the installer from the exact source
commit and point it at the candidate assets:

```sh
version=26.7.0
candidate_tag=26.7.0-rc.<short-sha>
source_sha=<full-source-sha>
curl -fsSL "https://raw.githubusercontent.com/VooZ2/kinkudos/$source_sha/deploy/install.sh" \
  -o /tmp/kinkudos-install.sh
KINKUDOS_VERSION="$version" \
KINKUDOS_RELEASE_BASE_URL="https://github.com/VooZ2/kinkudos/releases/download/v$candidate_tag" \
KINKUDOS_IMAGE_REPOSITORY="vooz2/kinkudos-rc" \
KINKUDOS_IMAGE_TAG="$candidate_tag" \
sh /tmp/kinkudos-install.sh
```

For upgrade acceptance testing, download both named assets from the candidate
prerelease, then pass the candidate image tag through `sudo` so the extracted
Compose files pull the RC image:

```sh
version=26.7.0
candidate_tag=26.7.0-rc.<short-sha>
gh release download "v$candidate_tag" --repo VooZ2/kinkudos \
  --pattern "kinkudos-$version.tar.gz" \
  --pattern "kinkudos-$version.tar.gz.sha256"
sha256sum -c "kinkudos-$version.tar.gz.sha256"
tar -xzf "kinkudos-$version.tar.gz"
sudo env KINKUDOS_IMAGE_REPOSITORY="vooz2/kinkudos-rc" \
  KINKUDOS_IMAGE_TAG="$candidate_tag" sh \
  "kinkudos-$version/deploy/install-release.sh" \
  "kinkudos-$version.tar.gz" \
  "kinkudos-$version.tar.gz.sha256" \
  "$version" \
  "$(pwd)/kinkudos-$version"
```

`KINKUDOS_IMAGE_REPOSITORY` and `KINKUDOS_IMAGE_TAG` are explicit
release-candidate-only overrides. During acceptance testing, pass both again to
every Compose command that resolves or recreates images, for example:

```sh
sudo env KINKUDOS_IMAGE_REPOSITORY="vooz2/kinkudos-rc" \
  KINKUDOS_IMAGE_TAG="$candidate_tag" docker compose pull
sudo env KINKUDOS_IMAGE_REPOSITORY="vooz2/kinkudos-rc" \
  KINKUDOS_IMAGE_TAG="$candidate_tag" docker compose up -d --force-recreate
```

These overrides do not need to be persisted in the production `.env`. They are
not part of the normal stable-user update workflow: after `26.7.0` is
published, the Compose defaults are the production `vooz2/kinkudos` package and
`26.7.0`, so no RC override is required.

Record the workflow's source SHA, candidate manifest digest, both image
architectures, prerelease asset URLs, and checksum before beginning VPS tests.
Candidate QA is not stable-release authorization: do not merge to `main`,
create a stable `v<version>` tag, publish stable image aliases, or deploy from
the candidate workflow.
