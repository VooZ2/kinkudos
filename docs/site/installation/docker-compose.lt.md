---
title: KinKudos diegimas su Docker Compose
description: Įdiekite KinKudos naudodami oficialius Compose servisus, nuolatinius serverio katalogus, sugeneruotas paslaptis ir turimą HTTPS reverse proxy.
---

# Diegimas su Docker Compose

Šis kelias skirtas patyrusiems savarankiško diegimo naudotojams, integruojantiems KinKudos į turimą Linux, NAS, Docker ar reverse proxy aplinką. Palaikomas diegimas naudoja leidime esančius `deploy/` failus; nekopijuokite pavienės Compose ištraukos be jai reikalingų paslapčių, scenarijų ir proxy papildinio.

## Diegimo struktūra

```text
kinkudos/
├── app/            # išsaugotas leidimo kodas
├── deploy/         # Compose, aplinka ir valdymo scenarijai
├── data/           # SQLite duomenų bazė ir privati medija
├── backups/        # vietinės DB kopijos
├── backup-state/   # kopijų būsenos duomenys
└── secrets/        # setup, Django, VAPID, SMTP ir kopijų paslaptys
```

Pagrindinis Compose failas paleidžia `app` ir `backup-agent`, bet neviešina programos prievado. Pasirinkite vieną palaikomą papildinį:

- `host` paskelbia `127.0.0.1:8000` serveryje veikiančiam Caddy ar Nginx;
- `traefik` prideda Traefik maršrutą ir išorinį tinklą;
- `container` prijungia prie esamo Nginx Proxy Manager ar kito proxy tinklo.

Niekada neviešinkite `8000` prievado internete. HTTPS turi užbaigti proxy, perduodantis tikrą domeną ir protokolą.

## Diegimas

Saugiausia rankinė eiga – parsisiųsti konkretaus GitHub leidimo archyvą ir SHA256 failą, juos patikrinti, nukopijuoti leidimo `deploy` katalogą ir paleisti tos versijos `bootstrap.sh`. Tikslios komandos prižiūrimos techniniame [diegimo apraše](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.lt.md#rankinis-patikrintas-diegimas).

Paruošimo scenarijus klausia tik kalbos, domeno ir jau veikiančio proxy režimo. Jis sugeneruoja paslaptis bei `.env`, patikrina Compose konfigūraciją, parsiunčia pilna versija pažymėtą atvaizdą ir paleidžia servisus.

Gavę HTTPS adresą ir privatų setup kodą tęskite [pirmąjį paruošimą naršyklėje](first-time-setup.lt.md).

## Nuolatiniai duomenys ir paslaptys

Kopijuokite `data`, reikalingą privačią mediją ir atskirai saugomas nuotolinėms kopijoms iššifruoti būtinas paslaptis. Niekada nekelkite `.env`, `secrets`, duomenų bazių, kopijų ar įkeltų failų į Git. Konteinerio pašalinimas ar perkūrimas neturi pašalinti šių serverio katalogų.

Vėliau naudokite [atnaujinimo](updating.lt.md), [kopijų](../backups.lt.md), [CLI](../administration/cli.lt.md) ir [problemų sprendimo](../troubleshooting.lt.md) vadovus.
