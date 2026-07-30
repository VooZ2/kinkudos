# Diegimas

Šis katalogas serveryje laikomas greta programos kodo ir paslapčių katalogų:

```text
kinkudos/
├── app/
├── deploy/
└── secrets/
```

## Paslaptys

`secrets` kataloge saugomi Django, VAPID, atsarginių kopijų ir, jei įjungtas
el. paštas, SMTP slaptažodžiai. Failai turi priklausyti serverio
administratoriui, turėti `0600` teises ir niekada nepatekti į Git.

## Diegimas

Reikalavimai:

- 64 bitų ARM arba x86 Linux serveris su Docker Engine ir Docker Compose;
- jau veikiantis Traefik, prijungtas prie išorinio Docker tinklo `web`;
- į serverį nukreiptas domeno vardas.
- kol repozitorija privati, GitHub CLI, prijungtas prie paskyros, kuri gali
  skaityti `VooZ2/kinkudos`.

Leidimo programos kodą laikykite `app`, o šį katalogą – greta jo, kaip parodyta
aukščiau. `deploy/.env` faile nustatykite `KINKUDOS_HOSTNAME` ir, jei reikia,
`KINKUDOS_ALLOWED_NETWORKS`, tada paleiskite:

```bash
cd /kelias/iki/kinkudos/deploy
./bootstrap.sh
```

Diegiklis paprašo pasirinkti anglų arba lietuvių kalbą, sugeneruoja trūkstamas
paslaptis, sukuria `.env`, pastato atvaizdą ir gali sukurti pirmąją šeimą.
Jau esančių paslapčių jis neperrašo.

Jei šeimos kūrimą praleidote:

```bash
docker compose exec app python manage.py setup_family --language lt
```

Kalbą vėliau galima pakeisti pačioje programoje; pasirinkimas išsaugomas tame
įrenginyje.

## Atnaujinimas į 0.12.4

Šias komandas paleiskite diegimo šakniniame kataloge, kuriame yra `app`,
`deploy`, `data` ir `secrets`:

```bash
gh release download v0.12.4 --repo VooZ2/kinkudos \
  --pattern 'kinkudos-0.12.4.tar.gz*'
sha256sum -c kinkudos-0.12.4.tar.gz.sha256
tar -xOf kinkudos-0.12.4.tar.gz \
  kinkudos-0.12.4/deploy/compose.yml > deploy/compose.yml
./deploy/install-release.sh \
  "$PWD/kinkudos-0.12.4.tar.gz" \
  "$PWD/kinkudos-0.12.4.tar.gz.sha256" \
  0.12.4 \
  "$PWD"
```

Atnaujintojas patikrina kontrolinę sumą ir leidimo duomenis, pastato ir
išbando atvaizdą, sukuria veikiančios duomenų bazės kopiją, tik tada perjungia
programą ir patikrina konteinerio būklę. Leidimo archyve nėra `deploy/.env`,
šeimos duomenų, nuotraukų, kopijų ar paslapčių.

## Kopijos

Prieš pirmą išorinę `restic` kopiją inicializuokite repozitoriją, tada
paleiskite kopijos skriptą:

```bash
docker compose --profile backup run --rm restic init
./backup.sh
```

Kopijų saugojimo trukmę ir tvarkaraštį pasirenka serverio administratorius.
Projektas nėra susietas su konkrečiu saugyklos tiekėju.

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

Kol SMTP nesukonfigūruotas, el. pašto funkcija yra išjungta.

Prisijungę tėvai ir vaikai problemą arba pasiūlymą gali pateikti plaukiojančiu
vabalo mygtuku. KinKudos pirmiausia išsaugo įrašą, o tik tada bando išsiųsti
el. laišką. Todėl tėvai atsiliepimą matys ir jo būseną galės keisti
„Nustatymuose“, net jei SMTP laikinai neveikia. Pasirinktinės ekrano nuotraukos
saugomos privačiai WebP formatu; pasibaigus nustatytam terminui automatiškai
šalinamos tik išspręstų atsiliepimų nuotraukos.

## Kasdienis nuotraukų valymas

KinKudos darbų nuotraukas ir išspręstų atsiliepimų ekrano nuotraukas saugo
tėvų nustatymuose pasirinktą laiką. `systemd` naudojančiame Docker serveryje
po diegimo įjunkite kasdienį valymą:

```bash
cd /kelias/iki/kinkudos/deploy
sudo ./install-maintenance.sh
```

## Ribota diagnostikos prieiga

Diagnostikos naudotojui nesuteikite narystės Docker grupėje. Administratorius
gali įdiegti root valdomą `kinkudos-diagnose` komandą, kuri parodo tik KinKudos
konteinerio būseną ir paskutines 300 žurnalo eilučių.
