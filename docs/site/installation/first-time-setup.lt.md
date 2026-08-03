---
title: Pirmasis KinKudos paruošimas naršyklėje
description: Naudodami vienkartinį setup kodą sukurkite šeimą, pirmą tėvų administratorių, pasirinkite kalbą, laiko zoną, išsaugokite atkūrimo kodą ir pasirinktinai nustatykite SMTP.
---

# Pirmasis paruošimas naršyklėje

Paleidę serverį atverkite installerio parodytą HTTPS adresą, pasibaigiantį `/setup/`. Neužbaigta instaliacija į šį puslapį automatiškai nukreipia ir iš įprastų programos puslapių.

!!! danger "Apsaugokite neužbaigtą instaliaciją"
    Paruošimą atlikite nedelsdami, naudokite HTTPS ir niekam neatskleiskite setup kodo. Prie naujos instaliacijos tinklo prieigą ir šį kodą turintis asmuo gali mėginti sukurti pirmą tėvų administratorių.

## Užpildykite formą

| Laukas | Ką įvesti |
|---|---|
| **Setup kodas** | Serverio installerio parodytą sudėtingą kodą. |
| **Tėvų naudotojo vardas** | Lengvai įsimenamą, unikalų pirmo suaugusiojo prisijungimo vardą. |
| **El. pašto adresas** | Galiojantį adresą. Įjungus SMTP jis naudojamas slaptažodžiui atkurti el. paštu. |
| **Slaptažodis** | Stiprų, unikalų slaptažodį, atitinkantį rodomas taisykles. |
| **Šeimos pavadinimas** | Privatų šeimos pavadinimą ar trumpinį, matomą šioje instaliacijoje. |
| **Numatytoji kalba** | Lietuvių arba anglų. Atskiruose įrenginiuose ją vėliau galima pakeisti. |
| **Laiko zona** | Tikrą šeimos laiko zoną, naudojamą datoms ir suplanuotiems veiksmams. |

### Neprivalomas el. pašto nustatymas

**Nustatyti el. paštą dabar** rinkitės tik turėdami tikslius SMTP duomenis. KinKudos veikia ir be SMTP, tačiau tuomet neveikia slaptažodžio atkūrimas el. paštu ir pasirinktiniai atsiliepimų laiškai.

Pasirinkus SMTP reikia nurodyti serverį, prievadą, saugos režimą, naudotoją, slaptažodį, siuntėjo ir atsiliepimų gavėjo adresus. Prieš užbaigdama formą KinKudos patikrina SMTP ryšį. Visų laukų paaiškinimai pateikti [SMTP vadove](../administration/smtp.lt.md).

## Išsaugokite atkūrimo kodą

Sėkmingai užbaigus paruošimą KinKudos prijungia tėvą ir vieną kartą parodo atkūrimo kodą. Prieš išeidami iš puslapio išsaugokite jį slaptažodžių tvarkyklėje. Vėliau kodas neberodomas ir yra būtinas KinKudos CLI atkūrimo komandai.

Setup puslapis tada visam laikui užrakinamas. Pakartotinai atvėrus `/setup/`, prisijungęs tėvas nukreipiamas į skydelį, o neprisijungęs lankytojas – į tėvų prisijungimą.

## Jei paruošimas nutrūko

Formai parodžius klaidą ją ištaisykite ir pateikite dar kartą. Tėvų paskyra, šeima ir užbaigimo žyma sukuriami vienoje transakcijoje, todėl formos ar SMTP ryšio klaida nepalieka dalinai sukurtos šeimos paskyros.

Jeigu setup puslapis neberodomas, nebandykite apeiti jo užrakto. Skaitykite [setup puslapio problemų](../troubleshooting.lt.md#setup-puslapis-nerodomas) arba jau veikiančiai instaliacijai naudokite dokumentuotą [slaptažodžio atkūrimą](../administration/password-recovery.lt.md).
