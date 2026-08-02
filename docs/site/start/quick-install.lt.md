# Diegimas paruoštame Docker serveryje

Šį būdą rinkitės naujai KinKudos instaliacijai serveryje, kuriame jau veikia „Docker Engine“, „Docker Compose“ įskiepis, domenas ir HTTPS reverse proxy, pavyzdžiui, „Traefik“, „Caddy“ ar „Nginx“.

> **Kam:** Serverio administratoriui<br>
> **Sudėtingumas:** Linux ir Docker administravimas<br>
> **Rezultatas:** Naujas KinKudos diegimas su pirmu šeimos paruošimu

> Tai diegimo vadovas žmogui, kuris prižiūri serverį. Kasdieniam KinKudos
> naudojimui tėvams jis nereikalingas.

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

Diegiklis parsiunčia naujausią paskelbtą leidimą, patikrina jo SHA256 sumą,
sukuria diegimo katalogą ir pradeda vedamą paruošimą. Kontrolinė suma patvirtina,
kad parsisiųstas archyvas sutampa su to paties leidimo paskelbta suma; tai nėra
atskira pasirašyta atestacija. Vedlys paklaus kalbos, domeno, proxy režimo,
šeimos pavadinimo, pirmos tėvų paskyros ir, jei norėsite, vaikų profilių.

Pabaigę patikrinkite konteinerių būseną ir atidarykite savo domeną per HTTPS,
tada prisijunkite pirmąja tėvų paskyra. Jei neveikia HTTPS, DNS arba
konteineris, sustokite ir naudokite diegimo diagnostiką, o ne paleiskite naujo
diegimo vedlį ant jau esančių failų.

## Ko šis diegiklis nedaro

- Jis nepakeičia esamos KinKudos instaliacijos. Esamam serveriui naudokite
  [atnaujinimą, kopijas ir atkūrimą](../server/updates-and-recovery.lt.md).
- Jis nesukuria už jus DNS įrašo ar reverse proxy.
- Jis nesiunčia šeimos duomenų į „GitHub“ ar „Docker Hub“. Paskelbtame „Docker“ atvaizde yra tik programa; duomenų bazė, nuotraukos, kopijos ir paslaptys lieka jūsų serveryje.

## Toliau

Tęskite su [Pirmomis 15 minučių](first-15-minutes.lt.md) ir paruoškite pirmą vaikų profilį praktiniam naudojimui.
