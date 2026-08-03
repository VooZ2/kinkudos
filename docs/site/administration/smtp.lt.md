---
title: Neprivalomo SMTP el. pašto nustatymas
description: Nustatykite ir patikrinkite neprivalomą KinKudos SMTP tėvų slaptažodžio atkūrimui bei privačių atsiliepimų pranešimams.
---

# SMTP nustatymas

SMTP neprivalomas. Darbai, taškai, prizai, vaikų prieiga ir privatūs programos atsiliepimai veikia ir be jo. SMTP įjungia tėvų slaptažodžio atkūrimą el. paštu ir pasirinktinius pranešimus apie išsaugotus privačius atsiliepimus.

SMTP galima nustatyti per [pirmąjį paruošimą](../installation/first-time-setup.lt.md) arba vėliau tėvų administratoriui atvėrus **Tėvai → Nustatymai → El. pašto nustatymai**. Vėliau keičiant duomenis reikia patvirtinti esamą KinKudos slaptažodį.

| Laukas | Reikšmė |
|---|---|
| **SMTP serveris** | Siunčiamų laiškų serverio vardas, pvz. `smtp.example.com`, be URL kelio. |
| **Prievadas** | Tiekėjo nurodytas prievadas; dažnai 587 STARTTLS arba 465 tiesioginiam SSL/TLS. |
| **Sauga** | STARTTLS/TLS, SSL/TLS arba „none“ rinkitės tiksliai pagal tiekėją. Nepatikimame tinkle nenaudokite nešifruoto ryšio. |
| **Naudotojo vardas** | SMTP prisijungimas, dažnai, bet ne visada, sutampantis su siuntėjo adresu. |
| **Slaptažodis** | SMTP ar programėlės slaptažodis. Jį reikia pakartoti kiekvieną kartą išsaugant pakeitimus. |
| **Siuntėjo adresas** | Gavėjams matomas adresas, kurį pašto tiekėjas paprastai turi leisti. |
| **Atsiliepimų gavėjas** | Pasirinktinis adresas pranešimams apie privačius atsiliepimus. |

Prieš išsaugodama KinKudos patikrina SMTP ryšį. Šiame leidime nėra atskirai dokumentuoto **Siųsti bandomąjį laišką** veiksmo. Tiekėjų reikalavimai keičiasi; vadovaukitės naujausiomis jų instrukcijomis ir prireikus naudokite programėlės slaptažodį.

Per UI valdomi nustatymai saugomi teisėmis apsaugotame `secrets/smtp/` faile; slaptažodis nelaikomas programos DB ir po išsaugojimo neberodomas. Nekelkite SMTP duomenų į Git, ekrano nuotraukas, pagalbos užklausas ar žurnalus.

Patyrę administratoriai gali naudoti leidimo `configure-email.sh` scenarijų arba palaikomą aplinkos fallback, aprašytą [techniniame diegimo vadove](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.lt.md#slaptazodzio-atkurimo-el-pastas).
