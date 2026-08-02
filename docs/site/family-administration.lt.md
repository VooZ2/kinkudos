# Šeimos administravimas

Šeimos administravimo skiltyje tėvai palaiko suprantamas paskyras, įrenginius
ir jautrias šeimos taisykles. Daugeliui šeimų jos reikia tik pridedant žmogų,
keičiant prieigą ar peržiūrint nustatymą, o ne kasdieniams darbų sprendimams.

> **Kam:** Tėvų administratoriams ir tėvams, valdantiems namų ūkio paruošimą<br>
> **Rezultatas:** Aiškios paskyrų, profilių, įrenginių ir nustatymų atsakomybės

## Supraskite tris vaidmenis

| Vaidmuo | Ką jis gali daryti |
| --- | --- |
| **Tėvai** | Naudoja skydelį, darbus, prizus, istoriją ir įprastus šeimos nustatymus. |
| **Tėvų administratorius** | Turi visas tėvų teises, taip pat tinklo prieigą, SMTP, kopijų duomenis ir rankinį kopijavimą bei visų vaiko įrenginių atšaukimą. Paprastai tai pirmas diegimo metu sukurtas tėvas. |
| **Vaikas** | Naudoja susietą naršyklę/PWA ir keturių skaitmenų PIN; mato savo duomenis bei bendrus katalogus, bet ne kitų vaikų privačią informaciją. |

Vienas suaugęs žmogus gali būti ir tėvų, ir serverio administratorius, tačiau
serverio vaidmuo papildomai apima Docker, HTTPS, atnaujinimus, prisijungimo
duomenis ir atkūrimą.

## Saugiai pridėkite arba išjunkite paskyras

**Tėvai → Nustatymai → Šeimos paskyros ir programos nustatymai** kiekvienam
suaugusiajam sukurkite atskirą tėvų paskyrą. Nesidalykite slaptažodžiais. El.
pašto adresas reikalingas slaptažodžio atkūrimui, kai sukonfigūruotas SMTP.

Pašalinus tėvą jo paskyra išjungiama, o istorija lieka. Paskutinio aktyvaus
tėvo pašalinti negalima. Pašalinus vaiką taip pat išjungiamas profilis ir
išsaugoma istorija; jo duomenys neperduodami kitam vaikui.

## Profilis, įrenginys ir PIN yra skirtingi dalykai

- **Vaiko profilis** saugo vardą, temą, avatarą, balansą, kredito ribą,
  gimtadienį, loterijos nustatymą ir istoriją.
- **Susietas įrenginys** yra konkreti naršyklė, telefonas, planšetė ar įdiegta
  PWA, kuriai leista rodyti vaikų profilius.
- **PIN** yra vaiko keturių skaitmenų prisijungimo žingsnis susietame įrenginyje.

Susiejus naują naršyklę nesukuriamas naujas vaikas. Atstačius PIN įrenginys
nesusiejamas. Saugią 10 minučių susiejimo nuorodos eigą rasite [vaiko įrenginio
susiejimo vadove](start/pair-a-child-device.lt.md).

## Jautrūs nustatymai yra pasirenkami

Tinklo leidžiamų adresų sąrašai, SMTP ir nuotolinės kopijos nereikalingi
kasdieniams darbams bei prizams. Prieš juos keisdami perskaitykite [tėvų
nustatymų vadovą](parents/settings.lt.md). Tėvų administratorius turi patvirtinti
savo slaptažodį prieš keičiant jautrią konfigūraciją.

## Atsiliepimai lieka šeimoje

Tėvai ir vaikai gali programoje išsaugoti privatų idėjos ar problemos pranešimą.
Jis lieka šeimos serveryje ir nėra siunčiamas KinKudos prižiūrėtojui. GitHub
Issues naudokite tik pakartojamai programos klaidai ir prieš tai pašalinkite
visus privačius šeimos duomenis.

[Tėvų nustatymai →](parents/settings.lt.md) · [Paskyros ir įrenginiai →](security/accounts-and-devices.lt.md) · [English](family-administration.md)
