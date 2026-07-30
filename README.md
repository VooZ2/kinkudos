# KinKudos

KinKudos is a self-hosted family PWA where children complete tasks, earn
theme-based points, and exchange them for rewards. Parents manage the shared
task, penalty, and reward catalogs and approve requests from a phone, tablet,
or desktop browser.

- **Current release:** 26.1.0
- **Languages:** English and Lithuanian
- **Platforms:** ARM64 and AMD64 Linux hosts with Docker

Lithuanian documentation: [README.lt.md](README.lt.md)

## What it includes

- PIN-based child profiles and password-protected parent accounts.
- Tasks with an approval workflow and optional private photo evidence.
- Rewards, penalties, savings goals, point gifts, and birthday awards.
- Seven child themes with their own names, visuals, sounds, and point units.
- Per-device language, sound, and Web Push notification controls.
- Append-only point history, private local data, and encrypted backup setup
  with health reporting.
- Installable PWA support for current desktop and mobile browsers.

KinKudos is production-ready for self-hosted single-family use. Existing
installations remain upgradeable, but operators should keep tested backups and
review release notes before updating.

## Deployment model

One KinKudos installation serves one family. The production configuration uses
Docker Compose, SQLite, Gunicorn, and an existing Traefik reverse proxy with an
external Docker network named `web`. TLS and access to trusted private networks
are handled by Traefik.

Application source is kept separately from runtime state:

```text
kinkudos/
├── app/       # release source
├── deploy/    # active Compose configuration
├── data/      # database and uploaded media
├── backups/   # local database backups
├── backup-state/ # backup health state
└── secrets/   # generated credentials and optional SMTP/restic secrets
```

Family data, uploads, databases, backups, `.env` files, and secrets must never
be committed to Git.

For initial installation and configuration details, see
[deploy/README.md](deploy/README.md). To update an existing KinKudos host,
download the desired archive and checksum from the repository's GitHub
Releases page, then run the bundled `deploy/install-release.sh` as documented
there.

## Local development

Python 3.12 is required. After creating a virtual environment and installing
`requirements.txt`:

```bash
python scripts/compile_translations.py
python manage.py migrate
python manage.py test economy.tests
python manage.py runserver
```

`seed_demo` is development-only and refuses to modify a non-empty database.

## Project documentation

- [Architecture and security](docs/ARCHITECTURE.md)
- [Deployment](deploy/README.md)
- [Release policy](docs/RELEASING.md)
- [Changelog](CHANGELOG.md) · [Lithuanian](CHANGELOG.lt.md)
- [MIT license](LICENSE)

## Disclaimer

KinKudos is an AI-created personal project made solely to experiment with
OpenAI Codex. It is provided as-is, without warranty or a promise of support,
fitness, or security for any particular use.
