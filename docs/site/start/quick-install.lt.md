# Greitas diegimas

Šį būdą rinkitės naujai KinKudos instaliacijai serveryje, kuriame jau veikia „Docker Engine“, „Docker Compose“ įskiepis, domenas ir HTTPS reverse proxy, pavyzdžiui, „Traefik“, „Caddy“ ar „Nginx“.

> Tai diegimo vadovas žmogui, kuris prižiūri serverį. Kasdieniam KinKudos naudojimui tėvams jis nereikalingas.

## Prieš pradedant

Įsitikinkite, kad turite:

- savo valdomą 64 bitų „Linux“ serverį (AMD64 arba ARM64);
- „Docker Engine“ ir `docker compose` įskiepį;
- į serverį nukreiptą domeną, pavyzdžiui, `seima.example.com`;
- HTTPS reverse proxy, priimantį šį domeną; ir
- įprastą serverio naudotoją, turintį teisę naudoti „Docker“. Diegiklio neleiskite kaip `root`.

## Paleiskite diegiklį

Paruoštame serveryje paleiskite:

```bash
curl -fsSL https://kinkudos.app/install.sh -o /tmp/kinkudos-install.sh && sh /tmp/kinkudos-install.sh
```

Diegiklis parsiunčia naujausią paskelbtą leidimą, patikrina jo SHA256 sumą, sukuria diegimo katalogą ir pradeda vedamą paruošimą. Jis paklaus kalbos, domeno, proxy režimo, šeimos pavadinimo, pirmos tėvų paskyros ir, jei norėsite, vaikų profilių.

Pabaigę atidarykite savo domeną per HTTPS ir prisijunkite pirmąja tėvų paskyra.

## Ko šis diegiklis nedaro

- Jis nepakeičia esamos KinKudos instaliacijos. Atnaujinimams naudokite [diegimo ir priežiūros vadovą](../deployment-and-maintenance.lt.md).
- Jis nesukuria už jus DNS įrašo ar reverse proxy.
- Jis nesiunčia šeimos duomenų į „GitHub“ ar „Docker Hub“. Paskelbtame „Docker“ atvaizde yra tik programa; duomenų bazė, nuotraukos, kopijos ir paslaptys lieka jūsų serveryje.

## Toliau

Tęskite su [Pirmomis 15 minučių](first-15-minutes.lt.md) ir paruoškite pirmą vaikų profilį praktiniam naudojimui.
