# KinKudos

A self-hosted family PWA where children earn points for tasks and achievements,
then exchange them for rewards.

The application supports English and Lithuanian. English is the default for new
installations; the browser language is detected automatically and every device
can save a different choice.

KinKudos runs on ARM64 and AMD64 Docker hosts. Family data and secrets are
never stored in the Git repository.

Lithuanian documentation: [README.lt.md](README.lt.md)

## Development

After creating a virtual environment and installing `requirements.txt`:

```bash
python scripts/compile_translations.py
python manage.py migrate
python manage.py test
python manage.py runserver
```

`seed_demo` is development-only and refuses to modify a non-empty database.

## Docker installation

```bash
cp deploy/.env.example deploy/.env
cd deploy
./bootstrap.sh
```

The installer asks for English or Lithuanian, builds the image, starts the
service, and can create generic parent and child accounts. See
[deploy/README.md](deploy/README.md) for deployment and SMTP details.

Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)  
Release policy: [docs/RELEASING.md](docs/RELEASING.md)  
Changelog: [CHANGELOG.md](CHANGELOG.md) · [Lithuanian](CHANGELOG.lt.md)
