# Diegimas

Šis katalogas serveryje laikomas greta programos kodo ir paslapčių katalogų:

```text
kinkudos/
├── app/
├── deploy/
└── secrets/
```

## Paslaptys

`secrets` kataloge saugomi Django, VAPID, atsarginių kopijų tarnybos,
`restic` ir, jei įjungtas el. paštas, SMTP slaptažodžiai. Failai turi priklausyti serverio
administratoriui, turėti `0600` teises ir niekada nepatekti į Git.

## Diegimas

Reikalavimai:

- 64 bitų ARM arba x86 Linux serveris su Docker Engine ir Docker Compose;
- jau veikiantis Traefik, prijungtas prie išorinio Docker tinklo `web`;
- į serverį nukreiptas domeno vardas;
- prieiga prie pasirinkto leidimo archyvo ir jo SHA256 kontrolinės sumos. Jei
  privačiai repozitorijai naudojamas GitHub CLI, jame turi būti prijungta tą
  repozitoriją galinti skaityti paskyra.

Leidimo programos kodą laikykite `app`, o šį katalogą – greta jo, kaip parodyta
aukščiau. `deploy/.env` faile nustatykite `KINKUDOS_HOSTNAME` ir, jei reikia,
`KINKUDOS_ALLOWED_NETWORKS`, tada paleiskite:

```bash
cd /kelias/iki/kinkudos/deploy
./bootstrap.sh
```

Diegiklis paprašo pasirinkti kalbą, domeną, leidžiamus privačius tinklus ir ar
iš karto kurti šeimą. Šeimos vedlys paprašo pirmos tėvų paskyros, šeimos
pavadinimo bei vaikų profilių. Sugeneruojamos trūkstamos paslaptys, sukuriamas
`.env` ir pastatomi atvaizdai. Jau esančių paslapčių diegiklis neperrašo.

Jei šeimos kūrimą praleidote:

```bash
docker compose exec app python manage.py setup_family --language lt
```

Kalbą vėliau galima pakeisti pačioje programoje; pasirinkimas išsaugomas tame
įrenginyje.

## Atnaujinimas iš leidimo archyvo

Šias komandas paleiskite diegimo šakniniame kataloge, kuriame yra `app`,
`deploy`, `data` ir `secrets`. `OWNER/REPOSITORY` bei versiją pakeiskite
norimo diegti leidimo reikšmėmis:

```bash
version=26.3.2
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

Atnaujintojas patikrina kontrolinę sumą ir leidimo duomenis, pastato ir
išbando atvaizdą, sukuria veikiančios duomenų bazės kopiją, tik tada perjungia
programą, patikrina konteinerio būklę ir atnaujina versijuojamus `deploy`
valdymo scenarijus. Vietinis `deploy/.env`, šeimos duomenys, nuotraukos,
kopijos ir paslaptys nekeičiami bei nepatenka į leidimo archyvą.

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

Prisijungę tėvai ir vaikai problemą arba pasiūlymą gali pateikti plaukiojančiu
vabalo mygtuku. KinKudos pirmiausia išsaugo įrašą, o tik tada bando išsiųsti
el. laišką. Todėl tėvai atsiliepimą matys ir jo būseną galės keisti
„Nustatymuose“, net jei SMTP laikinai neveikia. Pasirinktinės ekrano nuotraukos
saugomos privačiai WebP formatu; pasibaigus nustatytam terminui automatiškai
šalinamos tik išspręstų atsiliepimų nuotraukos.

## Periodinė priežiūra ir loterijos priminimai

KinKudos darbų nuotraukas ir išspręstų atsiliepimų ekrano nuotraukas saugo
tėvų nustatymuose pasirinktą laiką. Sistema taip pat kas 30 minučių patikrina,
ar jau reikia siųsti savaitinį loterijos priminimą. `systemd` naudojančiame
Docker serveryje po diegimo arba atnaujinimo į 26.3.2 įjunkite abu laikmačius:

```bash
cd /kelias/iki/kinkudos/deploy
sudo ./install-maintenance.sh
```

Bendriniame `cron` diegime naktinę priežiūrą paleiskite kartą per parą, o
priminimų komandą – kas 30 minučių:

```cron
15 2 * * * cd /kelias/iki/kinkudos/deploy && docker compose exec -T app python manage.py purge_task_evidence
*/30 * * * * cd /kelias/iki/kinkudos/deploy && docker compose exec -T app python manage.py send_lottery_reminders
```

## Ribota diagnostikos prieiga

Diagnostikos naudotojui nesuteikite narystės Docker grupėje. Administratorius
gali įdiegti root valdomą `kinkudos-diagnose` komandą, kuri parodo tik KinKudos
konteinerio būseną ir paskutines 300 žurnalo eilučių.

```bash
sudo ./install-diagnostics.sh SISTEMOS_NAUDOTOJAS
```
