# KinKudos diegimas į „Orange Pi“

Instrukcija skirta 64 bitų ARM „Orange Pi“ su „Armbian“, „Debian“ arba
„Ubuntu“. Komanda `uname -m` turi rodyti `aarch64`.

## Prieš pradedant

Reikia:

- veikiančio 64 bitų Linux ir atnaujintų sistemos paketų;
- „Docker Engine“ su `docker compose` papildiniu;
- domeno arba vidinio DNS vardo, nukreipto į „Orange Pi“;
- jau veikiančio „Traefik“ su išoriniu Docker tinklu `web`, `web` ir
  `websecure` įėjimais bei `letsencrypt` sertifikatų resolveriu;
- pakankamai vietos `data`, `backups` ir Docker atvaizdams;
- prieigos prie pasirinkto leidimo archyvo ir jo kontrolinės sumos.

Patikrinkite aplinką:

```bash
uname -m
docker version
docker compose version
docker network inspect web
```

Jei `web` tinklo dar nėra, jį sukurkite prieš paleisdami „Traefik“ ir
„KinKudos“:

```bash
docker network create web
```

## Leidimo paruošimas

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

`data`, `backups`, `backup-state`, `secrets` ir `deploy/.env` yra konkrečios
instaliacijos būsena. Jų negalima kelti į Git ar pakeisti kito leidimo
failais.

## Interaktyvus diegimas

```bash
cd /opt/kinkudos/deploy
./bootstrap.sh
```

Vedlys paprašys:

1. lietuvių arba anglų diegimo kalbos;
2. KinKudos domeno vardo;
3. leidžiamų privačių tinklų;
4. ar iš karto sukurti šeimą;
5. pirmo tėvų naudotojo vardo, el. pašto ir slaptažodžio;
6. šeimos pavadinimo;
7. vaikų profilių vardų ir PIN.

Pirmoji tėvų paskyra tampa administratoriumi ir vienintelė gali keisti
atsarginių kopijų prisijungimo duomenis.

Patikrinkite:

```bash
docker compose ps
docker compose logs --tail=100 app
docker compose logs --tail=100 backup-agent
```

Tada naršyklėje atidarykite `https://JŪSŲ-DOMENAS/`.

## Atsarginių kopijų nustatymas

Prisijunkite pirmąja tėvų paskyra ir atidarykite
„Nustatymai → Atsarginės kopijos“. „Backblaze B2“ sukurkite atskirą,
vienam bucket apribotą Application Key, o ne naudokite pagrindinį paskyros
raktą. Įveskite:

- S3 endpoint;
- bucket pavadinimą;
- regioną;
- Application Key ID;
- Application Key;
- dabartinį tėvų paskyros slaptažodį.

Paspaudus „Patikrinti ir išsaugoti“ saugykla patikrinama arba inicializuojama.
Po to paleiskite „Kurti kopiją dabar“. Žalias indikatorius turi atsirasti tik
po sėkmingo įkėlimo ir `restic check`.

Failą `/opt/kinkudos/secrets/restic_password` išsaugokite atskiroje
slaptažodžių tvarkyklėje ar neprisijungus laikomoje laikmenoje. Be jo
atsarginės kopijos po visiško serverio praradimo neatkursite.

## Atnaujinimas

Naudokite `deploy/README.lt.md` pateiktą `install-release.sh` eigą.
Atnaujintojas išsaugo `data`, nuotraukas, `.env`, SMTP, VAPID ir esamus
`restic` failus.

Prieš atnaujinimą vis tiek pasidarykite ir patikrinkite nepriklausomą kopiją.
