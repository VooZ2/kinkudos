---
title: KinKudos diegimas Hostinger VPS serveryje
description: Sukurkite Hostinger Ubuntu 24.04 Docker VPS, prijunkite domeną, paleiskite patikrintą KinKudos installerį su automatiniu Caddy HTTPS ir užbaikite paruošimą naršyklėje.
---

# Įdiekite KinKudos Hostinger VPS serveryje

Tai trumpiausias palaikomas naujo KinKudos serverio kelias. Installeris skirtas Hostinger **Ubuntu 24.04 su Docker** VPS šablonui, Browser Terminal lange vykdomas kaip `root`, paleidžia KinKudos su konkrečios versijos Caddy proxy, patikrina HTTPS ir parodo privatų pirmojo paruošimo kodą.

KinKudos nemokama. Hostinger VPS yra mokama, savarankiškai administruojama paslauga: jūs prižiūrite VPS, domeną, atnaujinimus ir patikrintas kopijas. Skirkite maždaug 30–60 minučių ir papildomo laiko galimam DNS atsinaujinimui.

## 1. Prieš pradėdami

Reikės:

- Hostinger paskyros ir mokėjimo priemonės;
- valdomo domeno arba subdomeno;
- prieigos prie jo DNS įrašų;
- Hostinger paskyrai skirto el. pašto adreso;
- slaptažodžių tvarkyklės serverio slaptažodžiui, setup ir atkūrimo kodams.

SMTP neprivalomas ir gali būti nustatytas vėliau.

[Peržiūrėti Hostinger VPS pasiūlymus](https://www.hostinger.com/lt?REFERRALCODE=LKIGEDIMICSU)

> **Partnerystės atskleidimas:** tai rekomendacinė nuoroda. Įsigijus paslaugą per ją, projekto prižiūrėtojas gali gauti komisinį atlyginimą be papildomos kainos jums. Hostinger nėra būtina KinKudos sąlyga, nėra oficialus projekto partneris ir neturi prieigos prie šeimos duomenų, išskyrus jūsų valdomą VPS paslaugą.

Rinkitės **VPS**, o ne bendrąjį Web Hosting. Planų pavadinimai ir kainos keičiasi; kol konkretus planas nepatikrintas realiame release bandyme, KinKudos nežada minimalaus Hostinger plano.

## 2. Sukurkite VPS

Kurdami VPS pasirinkite Hostinger **Ubuntu 24.04 su Docker** šabloną. Nenaudokite kitos operacinės sistemos: Hostinger diegimo profilis tikrina būtent šį šabloną.

Palaukite, kol hPanel parodys, kad VPS veikia. Saugiai išsaugokite jo viešą IPv4 adresą ir root prisijungimo duomenis.

## 3. Prijunkite domeną

Norimam adresui, pavyzdžiui, `seima.example.com`, sukurkite `A` įrašą, nukreiptą į VPS viešą IPv4 adresą. Jeigu DNS valdomas kitur, tokį pat įrašą sukurkite pas savo DNS tiekėją.

Naudokite tik mažosiomis raidėmis parašytą pilną domeną. Installeris nepriima IP adreso ar laikino HTTP adreso. DNS atsinaujinimas gali užtrukti.

Hostinger VPS firewall leiskite įeinančius TCP **80** ir **443** prievadus. Palikite SSH arba Browser Terminal prieigą. Neviešinkite `8000` prievado.

Prieš diegdami kompiuteryje patikrinkite, ar domenas jau nukreiptas į VPS:

```bash
getent hosts seima.example.com
```

Pavyzdį pakeiskite tikru adresu. Rezultate turi būti VPS IP.

## 4. Įdiekite KinKudos

Atverkite Hostinger **Browser Terminal**. Palaikomas šablonas pradžioje suteikia root prieigą, kurios šis specialus installeris ir tikisi.

Paleiskite viešą Hostinger installerį:

```bash
curl -fsSL https://kinkudos.app/install-hostinger.sh \
  -o /tmp/install-kinkudos-hostinger.sh \
  && sh /tmp/install-kinkudos-hostinger.sh
```

Mažas pradinis installeris suranda naujausią paskelbtą leidimą, iš GitHub parsiunčia jo archyvą ir SHA256 kontrolinę sumą, patikrina kontrolinę sumą bei archyvo kelius ir tik tada paleidžia pačiame leidime esantį Hostinger paruošimą. Norėdami prieš vykdymą peržiūrėti parsisiųstą scenarijų, atsisiuntimo ir `sh` komandas paleiskite atskirai.

Įveskite:

1. pradinę programos kalbą – `en` arba `lt`;
2. ankstesniame žingsnyje sukurtą tikslų domeną, be `https://` ir kelio.

Paruošimas patikrina Ubuntu, Docker ir Compose versijas, įsitikina, kad 80 bei 443 prievadai laisvi, sukuria `/opt/kinkudos`, sugeneruoja paslaptis ir paleidžia:

- privatų KinKudos `app` konteinerį;
- izoliuotą `backup-agent`;
- viešuose 80 ir 443 prievaduose veikiantį Caddy.

Caddy nukreipia HTTP į HTTPS, gauna ir atnaujina TLS sertifikatą. Sertifikato duomenys išlieka po įprastų atnaujinimų ir saugaus konteinerių pašalinimo.

## 5. Patikrinkite rezultatą

Installeris pateikia vieną iš trijų aiškių būsenų:

- **deployed and HTTPS ready** – galima tęsti;
- **deployed but HTTPS pending** – KinKudos ir Caddy veikia, bet DNS ar sertifikatas dar neparuoštas;
- **failed** – peržiūrėkite parodytą priežastį ir saugią žurnalų ištrauką.

Jei sertifikatas dar ruošiamas, patikrinkite DNS bei firewall 80/443 prievadus, kelias minutes palaukite ir vykdykite:

```bash
/opt/kinkudos/deploy/hostinger-healthcheck.sh /opt/kinkudos
```

Kai viskas veikia, installeris parodo:

```text
Setup URL: https://seima.example.com/setup/
Setup code: ...
```

Setup kodą laikykite paslaptyje. Jis galioja tik iki sėkmingo paruošimo pabaigos.

## 6. Užbaikite paruošimą naršyklėje

Atverkite parodytą HTTPS adresą ir atlikite [pirmąjį paruošimą naršyklėje](first-time-setup.lt.md). Sukurkite pirmą tėvų administratorių, įrašykite šeimos pavadinimą, pasirinkite kalbą bei laiko zoną ir nustatykite stiprų slaptažodį. Vienkartinį atkūrimo kodą išsaugokite slaptažodžių tvarkyklėje.

SMTP galite praleisti. KinKudos veiks, tačiau nebus el. pašto slaptažodžio atkūrimo ir pasirinktinių atsiliepimų laiškų. Vėliau naudokite [SMTP nustatymo vadovą](../administration/smtp.lt.md).

## 7. Pradėkite naudoti KinKudos

Pirmą vaiką, darbą ir prizą sukurkite pagal [pirmųjų 15 minučių vadovą](../start/first-15-minutes.lt.md). [Pranešimų ir PWA vadove](../security/notifications-and-pwa.lt.md) paaiškintas diegimas telefone.

Prieš patikėdami serveriui šeimos duomenis sukonfigūruokite [KinKudos atsargines kopijas](../backups.lt.md). Hostinger VPS snapshot saugo kitą sluoksnį ir nepakeičia programos kopijos.

Vėliau naudokite [atnaujinimo](updating.lt.md), [žurnalų ir diagnostikos](../administration/logs.lt.md) bei [problemų sprendimo](../troubleshooting.lt.md) vadovus.
