---
title: Vedamas KinKudos serverio installeris
description: Įdiekite patikrintą KinKudos leidimą paruoštame Linux serveryje, o pirmą tėvų paskyrą saugiai sukurkite naršyklėje.
---

# Vedamas serverio installeris

Šį būdą naudokite tik **naujai, tuščiai instaliacijai** serveryje, kuriame jau yra:

- 64 bitų AMD64 arba ARM64 Linux;
- Docker Engine ir Docker Compose papildinys;
- Docker prieigą turintis ne root diegimo naudotojas;
- į serverį nukreiptas domenas;
- HTTPS reverse proxy, pavyzdžiui, Caddy, Nginx, Nginx Proxy Manager ar Traefik.

Installeris neįdiegia Docker ir nesukuria reverse proxy. Jis atsisako naudoti netuščią diegimo katalogą ir nėra skirtas esamai instaliacijai atnaujinti.

## Peržiūrėkite ir paleiskite installerį

Prieš vykdydami galite [peržiūrėti installerio kodą](https://kinkudos.app/install.sh). Prisijungę diegimo naudotoju paleiskite:

```bash
curl -fsSL https://kinkudos.app/install.sh -o /tmp/kinkudos-install.sh \
  && sh /tmp/kinkudos-install.sh
```

Pradinis scenarijus suranda naujausią leidimą, parsiunčia jo archyvą ir SHA256 failą, patikrina kontrolinę sumą bei archyvo kelius, sukuria `/opt/kinkudos` ir paleidžia leidime esantį paruošimo scenarijų.

Pasirinkite:

1. diegimo kalbą (`en` arba `lt`);
2. tikslų viešą domeną;
3. jau paruošto proxy režimą: `host`, `traefik` arba `container`.

Installeris sugeneruoja serverio paslaptis, įrašo vietinį `.env`, parenka proxy papildinį, patikrina katalogų savininkus, parsiunčia konkrečios versijos programos atvaizdą ir paleidžia `app` bei `backup-agent`.

## Laukiamas rezultatas

Pabaigoje po konteinerių būsenos turi būti parodyta:

```text
Atverkite https://seima.example.com/setup/ ir naršyklėje įveskite šį setup kodą:
...
```

Setup kodą laikykite paslaptyje. Toliau atlikite [pirmąjį paruošimą naršyklėje](first-time-setup.lt.md). Terminale neįvedamas šeimos pavadinimas, tėvų slaptažodis ar vaikų PIN.

Jeigu konteineriai nepasileido, kataloge `/opt/kinkudos/deploy` vykdykite:

```bash
docker compose ps
docker compose logs --tail=100 app
```

Prieš dalydamiesi žurnalais pašalinkite paslaptis ir šeimos informaciją. Saugias patikras rasite [problemų sprendimo puslapyje](../troubleshooting.lt.md). Esamą instaliaciją atnaujinkite pagal [atnaujinimo vadovą](updating.lt.md).
