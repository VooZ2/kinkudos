# Leidimų taisyklės

Kiekvienas vartotojui matomas pakeitimas turi būti įtrauktas į
`CHANGELOG.md` dar prieš išleidžiant naują versiją.

## Versijos numerio parinkimas

Naudojama `YY.FEATURE.FIX` schema:

- `YY` – leidimo metų paskutiniai du skaitmenys, pvz. `26` reiškia 2026 m.;
- `FEATURE` – tais pačiais metais didinamas pridedant naują funkcionalumą;
- `FIX` – didinamas taisant klaidas, leidžiant pataisas, keičiant dizainą
  arba išplečiant jau esamą funkcionalumą.

Prasidėjus naujiems metams `YY` pakeičiamas, o kiti du skaičiai pradedami nuo
`0`. Produkciniai leidimai neturi `BETA` prierašo.

Pavyzdžiai:

- pirmas 2026 m. produkcinis leidimas yra `26.0.0`;
- `26.0.0` klaidos ar dizaino pataisa tampa `26.0.1`;
- naujas funkcionalumas po `26.0.1` tampa `26.1.0`;
- pirmas 2027 m. leidimas tampa `27.0.0`.

Vien dokumentacijos ar kūrimo proceso pakeitimas, kuris nekeičia įdiegtos
programos, naujos produkto versijos nereikalauja.

## Leidimo kontrolinis sąrašas

Kiekvienai versijai privaloma:

1. Pakeisti versiją `kinkudos/settings.py`, `pyproject.toml`, `deploy/compose.yml`,
   `README.md`, `README.lt.md` ir visuose leidimo atvaizdą nurodančiuose
   diegimo failuose.
2. `CHANGELOG.md` sukurti versijos antraštę su data.
3. Naujas funkcijas rašyti skiltyje `Added`.
4. Elgsenos pakeitimus rašyti skiltyje `Changed`, klaidų pataisymus –
   `Fixed`, o saugumo pakeitimus – `Security`.
5. Patikrinti, kad `/pakeitimai/` visa tai parodo kaip „Kas naujo?“ ir
   „Kas pataisyta?“.
6. Paleisti visus testus ir `python manage.py check`.
7. GitHub Release notes rašyti tik angliškai, išlaikant tokią pačią struktūrą
   kaip atitinkamas `CHANGELOG.md` leidimo įrašas. Leidimo tekstą galima
   tiesiogiai kopijuoti iš `CHANGELOG.md`.
8. Paskelbus versijos žymą palaukti, kol konteinerių darbo eiga sėkmingai
   pastatys AMD64 ir ARM64 atvaizdį ir publikuos jį į GHCR bei Docker Hub.
   Publikuojamos nekintamos pilnos versijos (pvz., `26.4.7`), einamosios
   pataisų serijos (pvz., `26.4`) ir `latest` žymos. Produkciniame diegime
   visada naudoti pilną versiją, o ne slankiąją žymą.

Versijos numeris programos antraštėje visada turi likti nuoroda į
`/pakeitimai/`.

Docker Hub publikavimui repozitorijos Actions secret `DOCKERHUB_TOKEN` turi
turėti tik Docker Hub access tokeno reikšmę, be vartotojo vardo ar `username:`
prefikso. Publikavimo paskyra yra `VooZ2`.
