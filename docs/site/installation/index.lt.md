---
title: KinKudos diegimas — pasirinkite tinkamą būdą
description: Palyginkite KinKudos diegimo būdus, reikalingus įgūdžius, serverio priežiūros atsakomybę ir pirmąjį paruošimą naršyklėje.
---

# Pasirinkite diegimo būdą

KinKudos diegiamas savarankiškai: kiekviena instaliacija veikia vienai šeimai
jos arba patikimo serverio administratoriaus pasirinktame ir prižiūrimame
Linux serveryje.

Pati programa yra nemokama, tačiau VPS ar kita hostingo paslauga gali kainuoti.

Nepriklausomai nuo pasirinkto būdo, diegimas susideda iš dviejų aiškių dalių:

1. paruošti serverį ir paleisti KinKudos konteinerius;
2. naršyklėje atverti `/setup/` ir sukurti šeimą bei pirmą tėvų paskyrą.

## Būdų palyginimas

| Būdas | Kam tinka | Terminalas | Ką prižiūrite |
|---|---|---:|---|
| [Hostinger VPS](hostinger.lt.md) | Norintiems paprasčiausio palaikomo Hostinger VPS kelio | Nereikia; naudojamas Docker Manager | VPS, atnaujinimus ir atsargines kopijas |
| [Vedamasis serverio diegiklis](guided-installer.lt.md) | Paruoštam Linux serveriui su Docker ir HTTPS proxy | Taip | Visą serverį |
| [Docker Compose](docker-compose.lt.md) | Patyrusiems savarankiško diegimo ar NAS naudotojams | Taip | Compose, paslaptis, proxy, saugyklą ir atnaujinimus |
| [Pažangus diegimas](advanced.lt.md) | Esamiems Traefik, Nginx Proxy Manager ar nestandartiniams Linux sprendimams | Taip | Visus integravimo sprendimus |

!!! warning "Prieš diegdami"
    Bendram diegimui reikia 64 bitų AMD64 arba ARM64 Linux serverio, Docker Engine, Docker Compose, domeno ir HTTPS atvirkštinio tarpinio serverio (proxy). Hostinger kelias naudoja Docker Manager ir su Ubuntu 24.04 with Docker šablonu įdiegtą Traefik proxy. Niekada neviešinkite KinKudos `8000` prievado.

Paleidę konteinerius tęskite [pradinį nustatymą naršyklėje](first-time-setup.lt.md).
