---
title: KinKudos žurnalai, diagnostika ir sveikatos patikros
description: Patikrinkite KinKudos ir kopijų agento būseną, saugiai surinkite žurnalus ir diagnozuokite Docker Manager ar proxy problemas neatskleisdami paslapčių ar šeimos duomenų.
---

# Žurnalai, diagnostika ir sveikatos patikros

Komandas vykdykite instaliacijos `deploy` kataloge.

## Konteinerių būsena

```bash
docker compose ps
```

`app` turi tapti sveikas. Bendrame Compose diegime taip pat turi veikti
`backup-agent`. Hostinger Docker Manager diegime valdomas Traefik yra už šio
Compose failo ribų.

Hostinger aplinkoje Docker Manager patikrinkite programą ir valdomą Traefik
maršrutą, tada HTTPS adresą atverkite naršyklėje.

## Naujausi žurnalai

```bash
docker compose logs --tail=100 app
docker compose logs --tail=100 backup-agent
```

Ribotai pagalbos paskyrai serverio administratorius gali įdiegti root valdomą `kinkudos-diagnose` scenarijų, užuot suteikęs Docker grupės teises. Diegimas aprašytas techniniame deploy vadove.

Prieš dalydamiesi pašalinkite naudotojų vardus, el. paštus, privačius domenus, jautrius IP, šeimos pavadinimus, užklausų turinį ir bet kokius tokenus ar prisijungimo duomenis. Niekada nesiųskite `.env`, DB, kopijų, paslapčių, setup ar atkūrimo kodų, privačių nuotraukų ir neredaguotų žurnalų.

## Saugus paleidimas iš naujo

```bash
docker compose restart app
docker compose ps
```

Netaisykite paleidimo klaidos trindami volumes ar serverio duomenis. Išsaugokite pradinę klaidą ir tęskite pagal [problemų sprendimo vadovą](../troubleshooting.lt.md).
