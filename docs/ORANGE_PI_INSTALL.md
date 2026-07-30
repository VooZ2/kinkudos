# Installing KinKudos on Orange Pi

This guide targets a 64-bit ARM Orange Pi running Armbian, Debian, or Ubuntu.
`uname -m` must report `aarch64`.

## Prerequisites

You need:

- an updated 64-bit Linux installation;
- Docker Engine with the `docker compose` plugin;
- a hostname routed to the Orange Pi;
- an existing Traefik instance with external Docker network `web`, `web` and
  `websecure` entrypoints, and a `letsencrypt` certificate resolver;
- enough storage for application data, backups, and Docker images;
- access to the selected release archive and its checksum.

Verify the host:

```bash
uname -m
docker version
docker compose version
docker network inspect web
```

Create the shared network if Traefik has not created it yet:

```bash
docker network create web
```

## Prepare the release

```bash
sudo mkdir -p /opt/kinkudos
sudo chown "$USER":"$USER" /opt/kinkudos
cd /opt/kinkudos

version=26.0.0
repository=OWNER/REPOSITORY
gh release download "v$version" --repo "$repository" \
  --pattern "kinkudos-$version.tar.gz*"
sha256sum -c "kinkudos-$version.tar.gz.sha256"

mkdir -p app deploy data backups backup-state secrets
tar -xzf "kinkudos-$version.tar.gz" --strip-components=1 -C app
cp -a app/deploy/. deploy/
```

The `data`, `backups`, `backup-state`, `secrets`, and `deploy/.env` paths are
installation state. Never commit them or replace them with another release.

## Interactive installation

```bash
cd /opt/kinkudos/deploy
./bootstrap.sh
```

The installer asks for the language, hostname, allowed private networks,
whether to create the family immediately, the first parent credentials, family
name, and child profile names and PINs. The first parent is the administrator
allowed to change backup credentials.

Verify the result:

```bash
docker compose ps
docker compose logs --tail=100 app
docker compose logs --tail=100 backup-agent
```

Open `https://YOUR-HOSTNAME/`.

## Configure backups

Sign in as the first parent and open Settings → Backups. For Backblaze B2,
create a dedicated application key restricted to one bucket instead of using
the master key. Enter the S3 endpoint, bucket, region, application key ID,
application key, and the current parent password.

After the storage is verified, run Back up now. The indicator becomes green
only after upload and `restic check` succeed.

Store `/opt/kinkudos/secrets/restic_password` in a separate password manager
or offline medium. A complete server loss cannot be recovered without it.

For upgrades, follow `deploy/README.md`. The updater preserves runtime data
and existing restic configuration.
