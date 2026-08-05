# Ką reiškia savarankiškas diegimas?

Savarankiškas diegimas reiškia, kad serverį, kuriame laikoma programa ir
privatūs šeimos duomenys, valdo jūsų šeima, o ne KinKudos. Tai suteikia kontrolę,
bet kartu ir atsakomybę už serverį.

> **Kam:** Žmogui, sprendžiančiam, kas prižiūrės KinKudos<br>
> **Sudėtingumas:** Pagrindinis serverio administravimas<br>
> **Reikia:** Linux, Docker, hosto vardo, HTTPS ir kopijų plano

## Namų serveris ar VPS

Savarankiškam diegimui nebūtina, kad fizinis serveris priklausytų jūsų šeimai.

KinKudos galima paleisti:

- fiziškai jūsų valdomame namų serveryje ar NAS;
- jūsų administruojamame nuomojamame VPS;
- patikimo žmogaus jūsų šeimos vardu prižiūrimame serveryje.

Naudojant VPS, fizinę infrastruktūrą valdo hostingo tiekėjas. Todėl taip pat
taikoma jo privatumo politika, saugumo priemonės, paskyros sąlygos, serverio
regionas ir teisinė jurisdikcija.

Savarankiškas diegimas reiškia, kad KinKudos projektas nevaldo jūsų šeimos
instaliacijos. Tai nereiškia, kad infrastruktūros tiekėjas visai nedalyvauja.

Rinkitės patikimą tiekėją ir turėkite kopijas, kurias galėtumėte atkurti kitur.

## Už ką atsako šeima

- kad veiktų serveris, domenas, HTTPS proxy ir Docker;
- kad būtų saugūs serverio bei tiekėjų prisijungimo duomenys;
- kad būtų diegiamas naujausias KinKudos leidimas;
- kad būtų sukonfigūruotos ir tikrinamos kopijos; ir
- kad būtų aišku, kas gali administruoti šeimą bei serverį.

KinKudos saugo programos duomenis privačiai tame diegime, bet negali apsaugoti
neatnaujinto, netyčia viešai atverto ar be atkuriamos kopijos prarasto serverio.

## Ko nereikia pirmą dieną

SMTP el. paštas, nuotolinės kopijos ir tinklo IP ribojimai yra vertingos
pasirenkamos paslaugos, bet jų nereikia, kad šeima sukurtų darbus, susietų vaiko
įrenginį ar naudotų taškus ir prizus. Juos įjunkite apgalvotai kartu su serverio
administratoriumi, neužblokuodami pirmo šeimos paruošimo.

## Praktinis atsakomybių pasidalijimas

| Žmogus | Įprasta atsakomybė |
| --- | --- |
| **Tėvai** | Naudoja darbus, prizus, sprendimus ir įprastus šeimos nustatymus. |
| **Tėvų administratorius** | Valdo jautrius programos nustatymus, susietus įrenginius ir šeimos paskyras. |
| **Serverio administratorius** | Prižiūri Docker, HTTPS, atnaujinimus, saugyklos duomenis, kopijas ir atkūrimą. Vienas žmogus gali atlikti visus tris vaidmenis. |

## Toliau

Jeigu toks atsakomybių pasidalijimas aiškus, peržiūrėkite [paruošto serverio
reikalavimus](../installation/guided-installer.lt.md) arba jau įdiegtą programą pradėkite naudoti
nuo [pirmų 15 minučių](first-15-minutes.lt.md).

[Grįžti į pradžią →](../index.lt.md) · [English](what-self-hosting-means.md)
