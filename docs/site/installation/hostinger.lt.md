---
title: Įdiekite KinKudos Hostinger VPS serveryje
description: Įdiekite KinKudos 26.5.2 naudodami Hostinger Docker Manager, valdomą Traefik atvirkštinį tarpinį serverį, HTTPS ir nuolatinį named volume.
---

# Įdiekite KinKudos Hostinger VPS serveryje

Tai paprasčiausias palaikomas Hostinger kelias. Naudojamas Hostinger VPS su
Docker Manager, Hostinger valdomas Traefik atvirkštinis tarpinis serveris ir
specialus KinKudos Compose failas iš `26.5.2` leidimo.

KinKudos Compose aprašas naudoja viešą `vooz2/kinkudos:26.5.2` atvaizdą ir
vieną nuolatinį named volume programos duomenų bazei, medijai bei vykdymo
paslaptims. Hostinger VPS yra mokama, jūsų administruojama paslauga: jūs
atsakote už VPS, domeną, atnaujinimus ir snapshot kopijas.

## 1. Prieš pradėdami

Reikės:

- Hostinger paskyros ir VPS su Docker Manager;
- jūsų valdomo domeno arba subdomeno;
- prieigos prie domeno DNS įrašų;
- VPS viešo IPv4 adreso;
- slaptažodžių tvarkyklės privačiam setup kodui, tėvų prisijungimo duomenims ir kitoms paslaptims saugoti.

KinKudos yra nemokama. Hostinger yra išorinis prieglobos tiekėjas ir nėra
oficialus KinKudos partneris.

[Peržiūrėti Hostinger VPS pasiūlymus](https://www.hostinger.com/lt?REFERRALCODE=LKIGEDIMICSU)

> **Partnerystės atskleidimas:** tai rekomendacinė nuoroda. Įsigijus paslaugą
> per ją, projekto prižiūrėtojas gali gauti komisinį atlyginimą be papildomos
> kainos jums.

## 2. Nukreipkite domeną į VPS

Sukurkite `A` įrašą norimam adresui, pavyzdžiui, `seima.example.com`, ir
nukreipkite jį į VPS viešą IPv4 adresą. Palaukite, kol DNS įrašas atsinaujins.

Hostinger palikite įjungtą valdomą Traefik ir jo HTTP/HTTPS prievadus.
Neviešinkite KinKudos `8000` prievado tiesiogiai — viešas įėjimas turi būti
Traefik.

## 3. Importuokite KinKudos Compose failą

Docker Manager sukurkite naują Compose programą ir importuokite tikslų faile
esantį aprašą:

```text
deploy/hostinger/compose.yaml
```

Failą galite peržiūrėti [GitHub](https://github.com/VooZ2/kinkudos/blob/main/deploy/hostinger/compose.yaml).
Jame aprašyta `app` paslauga, `vooz2/kinkudos:26.5.2` atvaizdas, Hostinger
Traefik žymos ir named volume `kinkudos-data`.

Prieš diegdami pateikite du šio Compose failo reikalaujamus kintamuosius:

```text
KINKUDOS_HOSTNAME=seima.example.com
KINKUDOS_SETUP_TOKEN=<ilgas-privatus-setup-kodas>
```

Įrašykite tikrą domeną ir sugeneruokite ilgą atsitiktinį setup kodą. Kodą
saugokite paslaptyje — jo reikės tik pirmai šeimai ir tėvų administratoriaus
paskyrai sukurti. Papildomų kintamųjų nepridėkite, nebent turite konkretų
palaikomą konfigūracijos poreikį.

## 4. Paleiskite ir užbaikite nustatymą naršyklėje

Docker Manager paspauskite **Deploy**. Hostinger valdomas Traefik turėtų
nukreipti domeną, peradresuoti HTTP į HTTPS ir gauti Let's Encrypt sertifikatą.
Atverkite:

```text
https://seima.example.com/setup/
```

Įveskite setup kodą ir naršyklėje sukurkite šeimą bei pirmą tėvų administratorių.
Tada prisijunkite ir patikrinkite, ar atsidaro tėvų skydelis.

## 5. Nuolatiniai duomenys ir priežiūra

Named volume `kinkudos-data` saugo SQLite duomenų bazę, įkeltą mediją ir
vykdymo paslaptis. Konteinerio perkrovimas, Compose priverstinis perkūrimas ir
VPS perkrovimas neturi jo pašalinti. Perkurdami Compose programą neištrinkite
šio volume.

Prieš reikšmingą pakeitimą sukurkite Hostinger VPS snapshot. Snapshot atkuria
visą VPS būseną. Šis kelias realiai patikrintas atliekant švarų diegimą,
HTTPS, pradinį naršyklės nustatymą, duomenų išlikimo, konteinerio ir VPS
perkrovimo, Compose perkūrimo, Docker Manager Update, snapshot sukūrimo ir
snapshot atkūrimo bandymus.

VPS snapshot nėra nešiojama aplikacijos lygio atsarginė kopija visiems
scenarijams. Jei reikia perkeliamumo ar atkūrimo ne Hostinger aplinkoje,
naudokite atskirą patikrintą KinKudos atsarginių kopijų strategiją.

Hostinger Compose faile sąmoningai nėra bendro KinKudos `backup-agent`, Restic
nustatymų ar papildomų kopijų paslapčių. Vėlesnei Hostinger priežiūrai naudokite
Docker Manager palaikomą atnaujinimo veiksmą ir prieš jį sukurkite snapshot.
Nemanykite, kad naujas Compose aprašas ar image tag pritaikomas automatiškai.

Naršyklės nustatymo laukų paaiškinimus rasite [pradinio nustatymo vadove](first-time-setup.lt.md).
