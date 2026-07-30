# KinKudos

Savarankiškai talpinama šeimos PWA, kurioje vaikai gauna taškus už darbus ir
pasiekimus, o vėliau keičia juos į prizus.

Programa veikia anglų ir lietuvių kalbomis. Naujos instaliacijos numatytoji
kalba yra anglų, tačiau atsižvelgiama į naršyklės kalbą, o kiekviename
įrenginyje pasirinkimą galima išsaugoti atskirai.

Projektas pritaikytas ARM64 ir AMD64 Docker aplinkoms. Šeimos duomenys bei
paslaptys Git repozitorijoje nelaikomi.

## Kūrimas

```bash
python scripts/compile_translations.py
python manage.py migrate
python manage.py test
python manage.py runserver
```

## Diegimas su Docker

```bash
cp deploy/.env.example deploy/.env
cd deploy
./bootstrap.sh
```

Diegiklis paprašo pasirinkti anglų arba lietuvių kalbą, pastato atvaizdą,
paleidžia servisą ir gali sukurti bendrines tėvų bei vaikų paskyras.
