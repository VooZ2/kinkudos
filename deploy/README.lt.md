# Diegimas

Šis katalogas serveryje laikomas greta programos kodo ir paslapčių katalogų:

```text
kinkudos/
├── app/                 # nebūtinas išsaugotas leidimo kodas
├── deploy/
├── data/
├── backups/
├── backup-state/
├── uploads/
└── secrets/
```

## Paslaptys

`secrets` kataloge saugomi Django, VAPID, atsarginių kopijų tarnybos,
`restic` ir, jei įjungtas el. paštas, SMTP slaptažodžiai. Failai turi priklausyti serverio
administratoriui, turėti `0600` teises ir niekada nepatekti į Git.

## Diegimas

Reikalavimai:

- tuščias 64 bitų ARM arba x86 Linux serveris ir administratoriaus paskyra su
  `sudo` teisėmis;
- HTTPS reverse proxy: „Nginx“, „Caddy“, „Nginx Proxy Manager“, „Traefik“ arba
  lygiavertis sprendimas;
- į serverį nukreiptas domeno vardas;
- prieiga prie pasirinkto leidimo archyvo ir jo SHA256 kontrolinės sumos. Jei
  privačiai repozitorijai naudojamas GitHub CLI, jame turi būti prijungta tą
  repozitoriją galinti skaityti paskyra;
- prieiga prie viešo `vooz2/kinkudos` „Docker Hub“ atvaizdo.

### Greitas diegimas paruoštame serveryje

Šį variantą naudokite naujame serveryje, kuriame jau veikia „Docker Engine“,
„Docker Compose“ papildinys, į serverį nukreiptas domenas ir palaikomas HTTPS
reverse proxy:

```bash
curl -fsSL https://kinkudos.app/install.sh -o /tmp/kinkudos-install.sh && sh /tmp/kinkudos-install.sh
```

Diegiklis nustato naujausią leidimą, parsisiunčia jo archyvą ir kontrolinę
sumą, patikrina SHA256, sukuria `/opt/kinkudos` ir paleidžia vedamą paruošimą.
Paleiskite jį įprasto diegimo naudotojo, o ne root vardu. Konkrečiam leidimui
naudokite `KINKUDOS_VERSION`, o kitam šakniniam katalogui –
`KINKUDOS_INSTALL_ROOT`.

Ši komanda skirta tik naujai instaliacijai. Jei KinKudos jau įdiegta,
naudokite [esamos instaliacijos atnaujinimą](#esamos-instaliacijos-atnaujinimas).

### Tuščio „Ubuntu“ serverio paruošimas

Toliau pateiktos komandos paruošia dabartinę palaikomą „Ubuntu Server“ versiją.
Kitoje Linux distribucijoje vadovaukitės oficialia
[Docker Engine diegimo instrukcija](https://docs.docker.com/engine/install/) ir
įdiekite Docker Compose papildinį (senas atskiras `docker-compose` failas
nenaudojamas). Palikite veikiančią SSH prieigą ir į serverį įleiskite HTTP bei
HTTPS srautą per 80 ir 443 prievadus. Neviešinkite 8000 prievado internete.

„Docker Engine“ ir Compose papildinį įdiekite iš oficialios Docker Apt
saugyklos:

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

Narystė `docker` grupėje suteikia root lygiavertę serverio prieigą. Atsijunkite
ir prisijunkite iš naujo, tada patikrinkite abu komponentus:

```bash
docker run --rm hello-world
docker compose version
```

„GitHub CLI“ įdiekite iš oficialios Apt saugyklos:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null
sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
  | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
sudo apt update
sudo apt install -y gh
```

Viešiems leidimams ir viešam „Docker Hub“ atvaizdui prisijungti prie registro
nereikia. Jei GitHub repozitorija privati, paleiskite `gh auth login`.

Paprasčiausiam serveryje veikiančio proxy variantui įdiekite „Caddy“ iš jo
oficialios saugyklos. Galite pasirinkti kitą palaikomą proxy ir
`bootstrap.sh` nurodyti jam tinkantį režimą.

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https gnupg
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
  | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
  | sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg \
  /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

Prieš tikėdamiesi TLS sertifikato patikrinkite, kad pasirinktas domenas jau
nukreiptas į šį serverį.

### Rankinis patikrintas diegimas

Diegdami rankiniu būdu, naujame tuščiame diegimo šakniniame kataloge
parsisiųskite ir patikrinkite konkretų leidimą, jo kodą palikite kaip `app`,
iškelkite diegimo katalogą ir paleiskite tą patį vedamą paruošimą:

```bash
sudo install -d -o "$USER" -g "$(id -gn)" /opt/kinkudos
cd /opt/kinkudos
version=26.4.9
repository=VooZ2/kinkudos
gh release download "v$version" --repo "$repository" \
  --pattern "kinkudos-$version.tar.gz*"
sha256sum -c "kinkudos-$version.tar.gz.sha256"
tar -xzf "kinkudos-$version.tar.gz"
mv "kinkudos-$version" app
cp -a app/deploy ./deploy
cd deploy
./bootstrap.sh
```

Pasirinkę serveryje veikiančio „Caddy“ režimą, `/etc/caddy/Caddyfile` pavyzdžio
domeną pakeiskite diegiklyje įvestu domenu:

```caddyfile
family.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

Patikrinkite konfigūraciją ir perkraukite „Caddy“:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Atverkite `https://family.example.com`, pakeitę jį tikruoju domenu. Diegimo
pabaigoje vedlys parodo konteinerių būseną; vėliau ją ir programos žurnalą
galite patikrinti komandomis `docker compose ps` bei
`docker compose logs --tail=100 app`.

Diegiklis paprašo pasirinkti kalbą, domeną, reverse proxy režimą ir ar iš karto
kurti šeimą. Šeimos vedlys paprašo pirmos tėvų paskyros, šeimos pavadinimo bei
vaikų profilių. Sugeneruojamos trūkstamos paslaptys, sukuriamas `.env`,
patikrinama serverio katalogų nuosavybė ir parsiunčiamas paskelbtas programos
atvaizdas. Jau esančių paslapčių diegiklis neperrašo.

Jei šeimos kūrimą praleidote:

```bash
docker compose exec app python manage.py setup_family --language lt
```

Kalbą vėliau galima pakeisti pačioje programoje; pasirinkimas išsaugomas tame
įrenginyje.

## Esamos instaliacijos atnaujinimas

Šias komandas paleiskite diegimo šakniniame kataloge, kuriame yra `app`,
`deploy`, `data` ir `secrets`. `OWNER/REPOSITORY` bei versiją pakeiskite
norimo diegti leidimo reikšmėmis:

```bash
version=26.4.9
repository=VooZ2/kinkudos
gh release download "v$version" --repo "$repository" \
  --pattern "kinkudos-$version.tar.gz*"
sha256sum -c "kinkudos-$version.tar.gz.sha256"
install_script="$(mktemp)"
compose_file="$(mktemp)"
tar -xOf "kinkudos-$version.tar.gz" \
  "kinkudos-$version/deploy/install-release.sh" > "$install_script"
tar -xOf "kinkudos-$version.tar.gz" \
  "kinkudos-$version/deploy/compose.yml" > "$compose_file"
sudo install -m 0644 "$compose_file" deploy/compose.yml
sudo sh "$install_script" \
  "$PWD/kinkudos-$version.tar.gz" \
  "$PWD/kinkudos-$version.tar.gz.sha256" \
  "$version" \
  "$PWD"
rm -f "$install_script" "$compose_file"
```

Atnaujintojas patikrina kontrolinę sumą ir leidimo duomenis, parsiunčia bei
išbando paskelbtą atvaizdą, patikrina serverio katalogų nuosavybę, sukuria
veikiančios duomenų bazės kopiją, tik tada perjungia programą, patikrina
konteinerio būklę ir atnaujina versijuojamus `deploy` valdymo scenarijus.
Vietinis `deploy/.env`, šeimos duomenys, nuotraukos, kopijos ir paslaptys
nekeičiami bei nepatenka į leidimo archyvą.

## Reverse proxy ir kliento IP

Bazinis Compose failas neviešina programos prievado ir nėra susietas su vienu
proxy produktu. `bootstrap.sh` sukuria vietinį `compose.override.yml`:

- `compose.host-proxy.yml` paskelbia `127.0.0.1:8000` serveryje įdiegtam
  „Nginx“ arba „Caddy“;
- `compose.container-proxy.yml` prijungia programą prie pasirenkamo išorinio
  Docker tinklo „Nginx Proxy Manager“ ar kitam konteineriniam proxy;
- `compose.traefik.yml` prideda KinKudos „Traefik“ maršrutą ir pasirinktą
  išorinį Docker tinklą.

Serveryje veikiančiame „Nginx“ nukreipkite į `http://127.0.0.1:8000` ir
perduokite pradinius `Host`, `X-Forwarded-Proto` bei `X-Forwarded-For`
antraščių duomenis:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

Minimalus „Caddy“ aprašas:

```caddyfile
family.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

„Nginx Proxy Manager“ pasirinkite Docker tarnybą `app`, prievadą `8000`,
įjunkite „WebSocket“ palaikymą ir naudokite tą patį išorinį tinklą, kuris
nurodytas `KINKUDOS_PROXY_NETWORK`.

KinKudos pasitiki persiųsta kliento IP antrašte tik jei tiesioginis ryšys
ateina iš `KINKUDOS_TRUSTED_PROXIES` nurodyto adreso ar potinklio. Nurodykite
tikslų proxy adresą arba Docker potinklį, o ne visą internetą. Pasirenkamas tėvų
nustatymas „Nustatymai → Tinklo prieiga“ gali papildomai apriboti vaikų
puslapius arba visą programą konkrečiais IP/CIDR tinklais. Pagal nutylėjimą jis
išjungtas ir nepakeičia HTTPS, įrenginių susiejimo ar stiprių tėvų
slaptažodžių. Jei taisyklė užrakino visus tėvus, paleiskite:

```bash
docker compose exec -T app python manage.py disable_network_restrictions
```

„Django“ administravimo maršrutas pagal nutylėjimą išjungtas. Įprastas šeimos
administravimas lieka tėvų sąsajoje.

Prieš diegimą arba atnaujinimą `check-ownership.sh` patikrina, ar prijungtus
katalogus gali rašyti `APP_UID` ir `APP_GID` naudotojas. Jei randamas
neatitikimas, peržiūrėkite konkretų kelią ir vykdykite parodytą `chown`
komandą; nekeiskite viso diegimo šakninio katalogo nuosavybės rekursyviai.

## Kopijos

Izoliuotas `backup-agent` sukuria nuoseklią SQLite kopiją, įtraukia įkeltas
nuotraukas ir šifruotus snapshot siunčia į „Backblaze B2“ arba kitą su S3
suderinamą saugyklą. Ją pirmoji tėvų administratoriaus paskyra nustato
„Nustatymai → Atsarginės kopijos“. Atnaujinant esamas
`secrets/restic.env` perkeliamas į `secrets/backup/restic.env`, o
`secrets/restic_password` išsaugomas.

Ši KinKudos valdoma nuotolinė kopija nėra tas pats, kas viso serverio arba
hostingo tiekėjo kopija. Programos sąsajoje rodoma tik KinKudos kopijų
tarnybos sukurta būsena. „Backblaze B2“ naudokite atskirą bucket ir tik jam
apribotą Application Key; leidimo patikrai naudokite atskirą testinį bucket
bei tik bandymų duomenis.

Jei išsaugant nustatymus pranešama, kad nepavyko rasti saugyklos serverio,
kopijų konteineriui nepavyko S3 adreso paversti IP adresu. Tai įvyksta dar
nepradėjus tikrinti prisijungimo duomenų. Patikrinkite, kad S3 adrese būtų tik
tiekėjo hostname (pavyzdžiui, `s3.eu-central-003.backblazeb2.com`), tada
patikrinkite DNS ir kopijų agento žurnalą:

Komandas paleiskite diegimo šakniniame kataloge, kuriame yra `deploy`
katalogas:

```bash
docker compose -f deploy/compose.yml exec -T backup-agent python -c \
  "import socket; print(socket.getaddrinfo('s3.eu-central-003.backblazeb2.com', 443))"
docker compose -f deploy/compose.yml logs --tail=100 backup-agent
```

Pavyzdžio hostname pakeiskite KinKudos įvestu adresu. Rezultatas
`Name or service not known` paprastai reiškia neteisingą arba neegzistuojantį
adresą; timeout ar `server misbehaving` rodo Docker daemon arba serverio
DNS / tinklo problemą.

Tą pačią patikrintą kopiją serveryje galima paleisti:

```bash
./backup.sh
```

Kopijos automatiškai kuriamos kartą per dieną po 03:00 serverio laiku.
Kitą valandą galima nustatyti `deploy/.env` reikšme `KINKUDOS_BACKUP_HOUR`.
Vietinės DB ir kasdienės nuotolinės kopijos laikomos 31 dieną; sėkminga būsena
įrašoma tik praėjus `restic check`.

`secrets/restic_password` kopiją laikykite atskirai nuo serverio. Atkūrimas
sąmoningai paliktas serverio administratoriui ir turi būti išbandytas atskirame
kataloge.

## Slaptažodžio atkūrimas el. paštu

Programa palaiko standartinį SMTP. Sukurkite atskirą KinKudos skirtą SMTP
prisijungimą ir paleiskite:

```bash
./configure-email.sh
```

Vedlys paprašo SMTP serverio, prievado, TLS/SSL režimo, naudotojo, siuntėjo
pavadinimo bei adreso ir adreso, kuriuo turi būti siunčiami pranešimai apie
išsaugotus atsiliepimus. Slaptažodis saugomas
`../secrets/smtp_password` faile su `0600` teisėmis, terminale nerodomas ir
nepatenka į komandų istoriją.

Kol SMTP nesukonfigūruotas, el. pašto funkcija yra išjungta. Vėliau tėvų
administratorius tuos pačius duomenis gali patikrinti ir pakeisti skiltyje
„Nustatymai“ → „El. paštas“, patvirtinęs pakeitimą dabartiniu savo
slaptažodžiu. Iš UI valdomos reikšmės, įskaitant slaptažodį, saugomos
`../secrets/smtp/settings.json` faile su `0600` teisėmis ir niekada
neįrašomos į programos duomenų bazę.

Prisijungę tėvai ir vaikai privačią šeimos problemą arba pasiūlymą gali pateikti
plaukiojančiu vabalo mygtuku. KinKudos pirmiausia išsaugo įrašą, o tik tada
bando išsiųsti el. laišką. Todėl tėvai atsiliepimą matys ir jo būseną galės
keisti „Nustatymuose“, net jei SMTP laikinai neveikia. Programos klaidos
registruojamos pateiktoje GitHub Issues nuorodoje; ten negalima siųsti vardų,
ekrano nuotraukų ar kitų šeimos duomenų. Pasirinktinės vidinės ekrano
nuotraukos saugomos privačiai WebP formatu; pasibaigus nustatytam terminui
automatiškai šalinamos tik išspręstų atsiliepimų nuotraukos.

## Periodinė priežiūra ir loterijos priminimai

KinKudos darbų nuotraukas ir išspręstų atsiliepimų ekrano nuotraukas saugo
tėvų nustatymuose pasirinktą laiką. Sistema taip pat kas 30 minučių patikrina,
ar jau reikia siųsti savaitinį loterijos priminimą. `systemd` naudojančiame
Docker serveryje po diegimo arba atnaujinimo įjunkite abu laikmačius:

```bash
cd /kelias/iki/kinkudos/deploy
sudo ./install-maintenance.sh
```

Bendriniame `cron` diegime naktinę priežiūrą paleiskite kartą per parą, o
priminimų komandą – kas 30 minučių:

```cron
15 2 * * * cd /kelias/iki/kinkudos/deploy && docker compose exec -T app python manage.py run_maintenance
*/30 * * * * cd /kelias/iki/kinkudos/deploy && docker compose exec -T app python manage.py send_lottery_reminders
```

Rankinis paleidimas:

```bash
docker compose exec -T app python manage.py run_maintenance
docker compose exec -T app python manage.py send_lottery_reminders
```

## Ribota diagnostikos prieiga

Diagnostikos naudotojui nesuteikite narystės Docker grupėje. Administratorius
gali įdiegti root valdomą `kinkudos-diagnose` komandą, kuri parodo tik KinKudos
konteinerio būseną ir paskutines 300 žurnalo eilučių.

```bash
sudo ./install-diagnostics.sh SISTEMOS_NAUDOTOJAS
```
