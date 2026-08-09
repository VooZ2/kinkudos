---
title: Vedamasis KinKudos serverio diegiklis
description: Įdiekite patikrintą KinKudos leidimą paruoštame Linux serveryje, o pirmą tėvų paskyrą saugiai sukurkite naršyklėje.
---

# Vedamasis serverio diegiklis

Šį būdą naudokite tik **naujam, tuščiam diegimui** serveryje, kuriame jau yra:

- 64 bitų AMD64 arba ARM64 Linux;
- Docker Engine ir Docker Compose papildinys;
- Docker prieigą turintis ne root diegimo naudotojas;
- į serverį nukreiptas domenas;
- HTTPS atvirkštinis tarpinis serveris (proxy), pavyzdžiui, Caddy, Nginx, Nginx Proxy Manager ar Traefik.

Diegiklis neįdiegia Docker ir nesukuria proxy. Jis atsisako naudoti netuščią diegimo katalogą ir nėra skirtas esamam diegimui atnaujinti.

Prieš paleisdami pasirinkite režimą pagal serveryje jau veikiantį proxy.
`host` rinkitės serveryje įdiegtam Caddy arba Nginx, `traefik` – veikiančiam
Traefik ir jo išoriniam Docker tinklui, o `container` – Docker veikiantiems
proxy, pavyzdžiui, Nginx Proxy Manager. Diegiklis tik parenka Compose papildinį:
jis nesukuria DNS įrašų, neįdiegia proxy ir nesukuria išorinio Docker tinklo.
Reikalavimus bei pavyzdžius rasite puslapyje [Proxy režimo pasirinkimas](docker-compose.lt.md#pries-diegikli-pasirinkite-proxy-rezima).

!!! warning "Docker prieiga yra privilegijuota"
    Docker prieiga praktiškai suteikia administracinę serverio kontrolę. Naudokite atskirą diegimo paskyrą, tačiau laikykite ją privilegijuota ir saugokite jos prisijungimo duomenis.

## Peržiūrėkite ir paleiskite diegiklį

Prieš vykdydami galite [peržiūrėti diegiklio kodą](https://kinkudos.app/install.sh). Prisijungę diegimo naudotoju paleiskite:

```bash
curl -fsSL https://kinkudos.app/install.sh -o /tmp/kinkudos-install.sh \
  && sh /tmp/kinkudos-install.sh
```

Pradinis scenarijus suranda naujausią leidimą, parsiunčia jo archyvą ir SHA256 failą, patikrina kontrolinę sumą bei archyvo kelius, sukuria `/opt/kinkudos` ir paleidžia leidime esantį paruošimo scenarijų.

Pasirinkite:

1. diegimo kalbą (`en` arba `lt`);
2. tikslų viešą domeną;
3. jau paruošto proxy režimą: `host`, `traefik` arba `container`.

Domeno paraginime įrašykite tik domeną, be `https://` ir be pasvirojo brūkšnio
pabaigoje. Proxy režimas turi atitikti prieš diegiklį paruoštą infrastruktūrą.

Diegiklis sugeneruoja serverio paslaptis, įrašo vietinį `.env`, parenka proxy papildinį, patikrina katalogų savininkus, parsiunčia pasirinktam KinKudos leidimui priskirtą programos atvaizdą ir paleidžia `app` bei `backup-agent`.

Diegikliui baigus darbą kataloge `/opt/kinkudos/deploy` vykdykite
`docker compose ps` ir prieš atverdami HTTPS domeną palaukite, kol `app` būsena
taps `healthy`.

## Laukiamas rezultatas

Pabaigoje po konteinerių būsenos turi būti parodyta:

```text
Atverkite https://seima.example.com/setup/ ir naršyklėje įveskite šį setup kodą:
...
```

Setup kodą laikykite paslaptyje. Toliau atlikite [pradinį nustatymą naršyklėje](first-time-setup.lt.md). Terminale neįvedamas šeimos pavadinimas, tėvų slaptažodis ar vaikų PIN.

Jeigu konteineriai nepasileido, kataloge `/opt/kinkudos/deploy` vykdykite:

```bash
docker compose ps
docker compose logs --tail=100 app
```

Prieš dalydamiesi žurnalais pašalinkite paslaptis ir šeimos informaciją. Saugias patikras rasite [problemų sprendimo puslapyje](../troubleshooting.lt.md). Esamą diegimą atnaujinkite pagal [atnaujinimo vadovą](updating.lt.md).
