# Leidimų taisyklės

Kiekvienas vartotojui matomas pakeitimas turi būti įtrauktas į
`CHANGELOG.md` dar prieš išleidžiant naują versiją.

## Versijos numerio parinkimas

Naudojama `MAJOR.MINOR.PATCH` schema:

- `MAJOR` – architektūriniai, esminiai logikos arba atgal nesuderinami
  pakeitimai;
- `MINOR` – naujos, su esama versija suderinamos funkcijos;
- `PATCH` – klaidų taisymai, dizaino pataisos ir smulkūs esamų funkcijų
  patobulinimai.

Kol produktas yra `0.x BETA`, naujos funkcijos didina `MINOR`, o pataisymai –
`PATCH`. `1.0.0` yra pirmas stabilus produkto leidimas ir nuo jo pašalinama
`BETA` žyma. Po stabilaus leidimo esminiai nesuderinami pakeitimai didina
`MAJOR`.

Pavyzdžiai:

- `0.8.0` klaidos pataisa tampa `0.8.1`;
- nauja beta funkcija tampa `0.9.0`;
- patvirtintas stabilus produktas tampa `1.0.0`;
- `1.0.0` pataisa tampa `1.0.1`;
- nauja suderinama funkcija tampa `1.1.0`;
- esminis nesuderinamas pakeitimas tampa `2.0.0`.

Vien dokumentacijos ar kūrimo proceso pakeitimas, kuris nekeičia įdiegtos
programos, naujos produkto versijos nereikalauja.

## Leidimo kontrolinis sąrašas

Kiekvienai versijai privaloma:

1. Pakeisti versiją `kinkudos/settings.py`, `pyproject.toml`, `deploy/compose.yml`
   ir `README.md`.
2. `CHANGELOG.md` sukurti versijos antraštę su data.
3. Naujas funkcijas rašyti skiltyje `Added`.
4. Elgsenos pakeitimus rašyti skiltyje `Changed`, klaidų pataisymus –
   `Fixed`, o saugumo pakeitimus – `Security`.
5. Patikrinti, kad `/pakeitimai/` visa tai parodo kaip „Kas naujo?“ ir
   „Kas pataisyta?“.
6. Paleisti visus testus ir `python manage.py check`.

Versijos numeris programos antraštėje visada turi likti nuoroda į
`/pakeitimai/`.
