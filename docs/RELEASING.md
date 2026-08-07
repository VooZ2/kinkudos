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
9. After creating the version tag, wait for the container workflow to build and
   publish both AMD64 and ARM64 images to GHCR and Docker Hub. The workflow
   publishes the immutable full version (for example `26.4.7`), the current
   patch series (for example `26.4`), and `latest`. Production deployments must
   always use the full version rather than a floating tag.
10. For deployment or setup changes, additionally validate:
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
11. For documentation changes, run a strict MkDocs build and validate internal
    and external links, old-URL redirects, canonical URLs, `hreflang`, the
    sitemap, `robots.txt`, and that every sitemap URL returns `200` directly.

Documentation changes to `docs.kinkudos.app`, the README, or other
documentation do not belong in the product changelog and do not change the
product version.

The version shown in the application header must always remain a link to
`/changes/`.

The repository Actions secret `DOCKERHUB_TOKEN` must contain only the Docker
Hub access-token value, without a username or `username:` prefix. The
publishing Docker ID is `vooz2`.
