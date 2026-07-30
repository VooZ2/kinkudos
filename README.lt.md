# KinKudos

KinKudos – savarankiškai talpinama šeimos PWA, kurioje vaikai atlieka darbus,
gauna teminius taškus ir keičia juos į prizus. Tėvai telefone, planšetėje ar
kompiuteryje valdo bendrus darbų, bausmių ir prizų sąrašus bei tvirtina vaikų
prašymus.

- **Dabartinis leidimas:** 0.12.4 BETA
- **Kalbos:** lietuvių ir anglų
- **Platformos:** ARM64 ir AMD64 Linux serveriai su Docker

## Kas įtraukta

- Vaikų profiliai su PIN ir slaptažodžiu apsaugotos tėvų paskyros.
- Tvirtinami darbai ir pasirinktinės privačios atlikto darbo nuotraukos.
- Prizai, bausmės, taupymo tikslai, taškų dovanos ir gimtadienio dovanos.
- Šešios vaikų temos su savais pavadinimais, vaizdais, garsais ir taškais.
- Atskirai kiekviename įrenginyje pasirenkama kalba, garsas ir pranešimai.
- Nekeičiamas taškų žurnalas, vietinis duomenų saugojimas ir kopijų įrankiai.
- Įdiegiama PWA šiuolaikinėms kompiuterių ir mobiliųjų įrenginių naršyklėms.

KinKudos vis dar yra BETA ir kasdien naudojamas vienoje šeimoje. Esamas
instaliacijas siekiama išlaikyti atnaujinamas, tačiau prieš diegiant leidimą
reikia turėti patikrintą atsarginę kopiją ir perskaityti pakeitimų sąrašą.

## Diegimo modelis

Viena KinKudos instaliacija skirta vienai šeimai. Produkcinėje aplinkoje
naudojami Docker Compose, SQLite, Gunicorn ir jau veikiantis Traefik reverse
proxy su išoriniu Docker tinklu `web`. TLS ir prieigą tik iš patikimų privačių
tinklų valdo Traefik.

```text
kinkudos/
├── app/       # leidimo programos kodas
├── deploy/    # aktyvi Compose konfigūracija
├── data/      # duomenų bazė ir įkeltos nuotraukos
├── backups/   # vietinės duomenų bazės kopijos
└── secrets/   # sugeneruotos paslaptys ir pasirinktiniai SMTP/restic duomenys
```

Šeimos duomenų, nuotraukų, duomenų bazių, kopijų, `.env` failų ir paslapčių
negalima kelti į Git.

Pirmojo diegimo ir konfigūravimo instrukcijos pateiktos
[deploy/README.lt.md](deploy/README.lt.md). Norint esamame KinKudos serveryje
įdiegti 0.12.4, reikia iš
[GitHub Releases](https://github.com/VooZ2/kinkudos/releases/tag/v0.12.4)
atsisiųsti leidimo archyvą bei jo kontrolinę sumą ir paleisti pridėtą
`deploy/install-release.sh`.

## Vietinis kūrimas

Reikalingas Python 3.12. Sukūrus virtualią aplinką ir įdiegus
`requirements.txt`:

```bash
python scripts/compile_translations.py
python manage.py migrate
python manage.py test economy.tests
python manage.py runserver
```

## Projekto dokumentai

- [Architektūra ir saugumas](docs/ARCHITECTURE.md)
- [Diegimas](deploy/README.lt.md)
- [Leidimų taisyklės](docs/RELEASING.md)
- [Pakeitimai](CHANGELOG.lt.md) · [angliškai](CHANGELOG.md)
- [MIT licencija](LICENSE)

## Atsakomybės apribojimas

KinKudos yra AI sukurtas asmeninis projektas, skirtas tik išbandyti OpenAI
Codex. Jis pateikiamas toks, koks yra, be garantijų, palaikymo pažado ar
patvirtinimo, kad tinka konkrečiam naudojimui arba yra visiškai saugus.
