---
title: Pradinis KinKudos nustatymas naršyklėje
description: Naudodami privatų setup kodą sukurkite šeimą, pirmą tėvų administratorių, pasirinkite kalbą, laiko zoną, išsaugokite atkūrimo kodą ir pasirinktinai nustatykite SMTP.
---

# Pradinis nustatymas naršyklėje

Paleidę serverį atverkite diegiklio parodytą HTTPS adresą, pasibaigiantį `/setup/`. Neužbaigtas diegimas į šį puslapį automatiškai nukreipia ir iš įprastų programos puslapių.

!!! danger "Apsaugokite neužbaigtą diegimą"
    Pradinį nustatymą atlikite nedelsdami, naudokite HTTPS ir niekam neatskleiskite setup kodo. Prie naujo KinKudos serverio tinklo prieigą ir šį kodą turintis asmuo gali mėginti sukurti pirmą tėvų administratorių.

## Užpildykite formą

| Laukas | Ką įvesti |
|---|---|
| **Setup kodas** | Serverio diegiklio parodytą sudėtingą kodą. |
| **Tėvų naudotojo vardas** | Lengvai įsimenamą, unikalų pirmo suaugusiojo prisijungimo vardą. |
| **El. pašto adresas** | Galiojantį adresą. Įjungus SMTP jis naudojamas slaptažodžiui atkurti el. paštu. |
| **Slaptažodis** | Stiprų, unikalų slaptažodį, atitinkantį rodomas taisykles. |
| **Šeimos pavadinimas** | Privatų šeimos pavadinimą ar trumpinį, matomą šiame KinKudos serveryje. |
| **Numatytoji kalba** | Lietuvių arba anglų. Atskiruose įrenginiuose ją vėliau galima pakeisti. |
| **Laiko zona** | Tikrą šeimos laiko zoną, naudojamą datoms ir suplanuotiems veiksmams. |

### Neprivalomas el. pašto nustatymas

**Nustatyti el. paštą dabar** rinkitės tik turėdami tikslius SMTP duomenis. KinKudos veikia ir be SMTP, tačiau tuomet neveikia slaptažodžio atkūrimas el. paštu ir pasirinktiniai atsiliepimų laiškai.

Pasirinkus SMTP reikia nurodyti serverį, prievadą, saugos režimą, naudotoją, slaptažodį, siuntėjo ir atsiliepimų gavėjo adresus. Prieš užbaigdama formą KinKudos patikrina SMTP ryšį. Visų laukų paaiškinimai pateikti [SMTP vadove](../administration/smtp.lt.md).

## Išsaugokite atkūrimo kodą

Sėkmingai užbaigus pradinį nustatymą KinKudos prijungia tėvą ir vieną kartą parodo atkūrimo kodą. Prieš išeidami iš puslapio išsaugokite jį slaptažodžių tvarkyklėje. Vėliau kodas neberodomas, tačiau galioja tol, kol yra pakeičiamas, ir yra būtinas KinKudos CLI atkūrimo komandai.

Setup puslapis tada visam laikui užrakinamas. Pakartotinai atvėrus `/setup/`, prisijungęs tėvas nukreipiamas į skydelį, o neprisijungęs lankytojas – į tėvų prisijungimą.

## Jei pradinis nustatymas nutrūko

Formai parodžius klaidą ją ištaisykite ir pateikite dar kartą. Tėvų paskyra, šeima ir užbaigimo žyma sukuriami vienoje transakcijoje, todėl formos ar SMTP ryšio klaida nepalieka dalinai sukurtos šeimos paskyros.

Jeigu setup puslapis neberodomas, nebandykite apeiti jo užrakto. Skaitykite [setup puslapio problemų](../troubleshooting.lt.md#setup-puslapis-nerodomas) arba jau veikiančiam KinKudos serveriui naudokite dokumentuotą [slaptažodžio atkūrimą](../administration/password-recovery.lt.md).
