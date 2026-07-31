# KinKudos

> Savarankiškai talpinama šeimos PWA, kasdienius darbus paverčianti bendrais pasiekimais.

**Dabartinis leidimas:** 26.4.2 · **Kalbos:** lietuvių ir anglų

## Kodėl KinKudos?

KinKudos vaikams suteikia aiškų ciklą: pasirinkti darbą, jį atlikti, gauti
teminių taškų ir siekti norimo prizo. Tėvai telefone, planšetėje ar
kompiuteryje valdo patvirtinimus, prizus, bausmes, kredito limitus ir bendrus
šeimos nustatymus.

Viena instaliacija skirta vienai šeimai. Programoje nėra reklamų ar integruotos
analitikos, o šeimos duomenys lieka savame serveryje, išskyrus operatoriaus
aiškiai įjungtas paslaugas, pavyzdžiui, Web Push, SMTP ar šifruotas nuotolines
kopijas.

## Kaip tai atrodo

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/welcome.jpg" alt="KinKudos pradžios ekranas"></td>
    <td width="50%"><img src="docs/screenshots/parent-dashboard.jpg" alt="KinKudos tėvų erdvė"></td>
  </tr>
  <tr>
    <td align="center"><sub>Paprastas įėjimas vaikams ir tėvams</sub></td>
    <td align="center"><sub>Tėvų suvestinė ir patvirtinimų eiga</sub></td>
  </tr>
</table>

<p>
  <img src="docs/screenshots/settings.png" alt="KinKudos tėvų nustatymai">
</p>
<p align="center"><sub>Šeimos, privatumo, tarnybų, paskyrų ir atsiliepimų nustatymai vienoje tėvų erdvėje</sub></p>

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/child-magic-academy.png" alt="KinKudos Magijos akademijos vaiko vaizdas"></td>
    <td width="50%"><img src="docs/screenshots/child-block-world.png" alt="KinKudos Blokų pasaulio vaiko vaizdas"></td>
  </tr>
  <tr>
    <td align="center"><sub>„Magijos akademijos“ vaiko tema</sub></td>
    <td align="center"><sub>„Blokų pasaulio“ vaiko tema</sub></td>
  </tr>
</table>

Ekrano nuotraukose naudojami išgalvoti demonstraciniai duomenys.

## Svarbiausios galimybės

- **Septynios vaikų temos** su originaliais vaizdais, garsais, tekstais ir
  taškų vienetais.
- **Tėvų valdoma šeimos ekonomika:** darbai, patvirtinimai, prizai, bausmės,
  taupymo tikslai, kiekvieno vaiko kredito limitas, dovanos ir gimtadienio
  taškai.
- **Prie temos pritaikyta nutrinama loterija** su aiškiomis laimėjimo ir
  praradimo tikimybėmis, keičiama pirkimo kaina bei savaitės limitu, bendrais
  ir kiekvieno vaiko valdikliais, išliekančiais bilietais ir tėvams matoma
  taškų istorija.
- **Privačios darbų nuotraukos**, kurios sumažinamos, konvertuojamos į WebP ir
  prieš saugojimą išvalomos nuo EXIF metaduomenų.
- **Įdiegiama PWA** su atskirais kiekvieno įrenginio kalbos, garso ir
  pasirinktinių Web Push pranešimų nustatymais. Neprisijungus pasiekiamas tik
  programos karkasas – privatūs balansai ir prašymai nekaupiami.
- **Lietuviška ir angliška sąsaja** tėvų bei vaikų veiksmuose.
- **Šifruotų kopijų integracija** su „Backblaze B2“ arba bendrine
  S3 suderinama saugykla per izoliuotą `restic` agentą, rodant kopijų būseną ir
  vientisumo patikrą.

## Privatumo ir saugumo modelis

- Tėvai jungiasi ribojamų bandymų slaptažodžiais. Prieš parodant vaikų
  profilius ar leidžiant įvesti ribojamų bandymų maišomą PIN, įrenginį turi
  patvirtinti tėvai; jo prieigą galima bet kada atšaukti.
- Konteineriai veikia be `root` teisių, programos konteinerio failų sistema yra
  tik skaitoma.
- Taškų operacijos yra transakcinės, o žurnalo įrašai nekeičiami.
- Įkeltos nuotraukos yra privačios ir šalinamos pagal pasirinktą saugojimo
  laiką.
- Prisijungimai, DB, nuotraukos, kopijos ir šeimos duomenys laikomi už leidimo
  kodo katalogo ribų.

KinKudos skirtas naudoti už TLS reverse proxy. Palaikomi „Nginx“, „Caddy“,
„Traefik“ ir konteineriniai proxy, tokie kaip „Nginx Proxy Manager“.
Pasirenkamas programos IP leidžiamų tinklų sąrašas gali riboti vaikų arba visos
instaliacijos prieigą. Už saugų serverį, patikrintą duomenų atkūrimą,
atnaujinimus ir prieigą prie hosto atsako operatorius.

## Diegimas

Palaikomoje produkcinėje schemoje naudojamas versijuotas kelių architektūrų
konteinerio atvaizdas, Docker Compose, SQLite, Gunicorn, izoliuotas kopijų
agentas ir operatoriaus pasirinktas TLS reverse proxy. Palaikomi ARM64 ir AMD64
Linux serveriai.

- [Diegimas ir atnaujinimas](deploy/README.lt.md)
- [Architektūra ir saugumas](docs/ARCHITECTURE.md)
- [Pakeitimų istorija](CHANGELOG.lt.md)

Leidimų archyvai ir jų kontrolinės sumos skelbiami
[GitHub Releases puslapyje](https://github.com/VooZ2/kinkudos/releases).
Kartu skelbiamas versijuotas `ghcr.io/vooz2/kinkudos` konteinerio atvaizdas.
Repozitorija neskelbia vienos komandos viešojo debesies diegimo.

## Vietinis kūrimas

Reikalingas Python 3.12. Sukūrus virtualią aplinką ir įdiegus
`requirements.txt`:

```bash
python scripts/compile_translations.py
python manage.py migrate
python manage.py test economy.tests
python manage.py runserver
```

`seed_demo` skirta tik kūrimui ir atsisako keisti netuščią duomenų bazę.

## Licencija

Platinama pagal [MIT licenciją](LICENSE).

## Atsakomybės apribojimas

KinKudos yra AI sukurtas asmeninis projektas, skirtas tik išbandyti OpenAI
Codex. Jis pateikiamas toks, koks yra, be garantijų, palaikymo pažado ar
patvirtinimo, kad tinka konkrečiam naudojimui arba yra visiškai saugus.
