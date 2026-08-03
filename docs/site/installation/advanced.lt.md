---
title: Pažangus KinKudos diegimas
description: Integruokite KinKudos į turimą Caddy, Nginx, Traefik ar Nginx Proxy Manager aplinką, išlaikydami patikimą proxy konfigūraciją ir privačius prievadus.
---

# Pažangus diegimas

Šis puslapis skirtas jau administruojantiems Docker ir HTTPS proxy. KinKudos nereikia atskiro tiekėjo atvaizdo: visi būdai naudoja tuos pačius konkrečia versija pažymėtus programos ir kopijų agento atvaizdus.

- Serveryje veikiantis Caddy ar Nginx: naudokite `host` papildinį ir proxy į `127.0.0.1:8000`.
- Traefik: naudokite pateiktą Traefik papildinį ir tikslų išorinį tinklą.
- Nginx Proxy Manager ar kitas konteinerinis proxy: naudokite `container` papildinį, servisą `app`, prievadą `8000` ir nustatytą išorinį tinklą.

Perduokite `Host`, `X-Forwarded-Proto` ir kliento IP antraštes. `KINKUDOS_TRUSTED_PROXIES` apribokite tikru proxy adresu ar Docker potinkliu; niekada nepasitikėkite visu internetu. Prieš paleisdami tikrinkite `docker compose config`, o `data`, kopijas ir paslaptis laikykite už leidimo kodo ribų.

Visos komandos ir proxy pavyzdžiai prižiūrimi [techniniame diegimo apraše](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.lt.md#reverse-proxy-ir-kliento-ip).
