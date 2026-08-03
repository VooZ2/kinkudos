---
title: KinKudos diegimas su Docker Compose
description: Įdiekite KinKudos naudodami oficialias Compose paslaugas, nuolatinius serverio katalogus, sugeneruotas paslaptis ir turimą HTTPS atvirkštinį tarpinį serverį.
---

# Diegimas su Docker Compose

Šis kelias skirtas patyrusiems savarankiško diegimo naudotojams, integruojantiems KinKudos į turimą Linux, NAS, Docker ar atvirkštinio tarpinio serverio (proxy) aplinką. Palaikomas diegimas naudoja leidime esančius `deploy/` failus; nekopijuokite pavienės Compose ištraukos be jai reikalingų paslapčių, scenarijų ir proxy papildinio.

## Diegimo struktūra

```text
kinkudos/
├── app/            # išsaugotas leidimo kodas
├── deploy/         # Compose, aplinka ir valdymo scenarijai
├── data/
│   ├── kinkudos.sqlite3  # SQLite duomenų bazė
│   └── media/            # privačios įkeltos nuotraukos
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

Paruošimo scenarijus klausia tik kalbos, domeno ir jau veikiančio proxy režimo. Jis sugeneruoja paslaptis bei `.env`, patikrina Compose konfigūraciją, parsiunčia pasirinktam KinKudos leidimui priskirtą atvaizdą ir paleidžia paslaugas.

Gavę HTTPS adresą ir privatų setup kodą tęskite [pradinį nustatymą naršyklėje](first-time-setup.lt.md).

## Nuolatiniai duomenys ir paslaptys

Kurkite viso `data/` katalogo atsargines kopijas: jame yra ir `kinkudos.sqlite3`, ir privačios įkeltos nuotraukos kataloge `data/media/`. Jei naudojate nuotolines atsargines kopijas, atskirai apsaugokite `secrets/restic_password` ir `secrets/backup/restic.env` — juose yra slaptažodis ir saugyklos nustatymai, reikalingi toms kopijoms pasiekti. Niekada nekelkite `.env`, `secrets`, duomenų bazių, atsarginių kopijų ar įkeltų failų į Git. Konteinerio pašalinimas ar perkūrimas neturi pašalinti šių serverio katalogų. Palaikoma eiga aprašyta [atsarginių kopijų ir atkūrimo vadove](../backups.lt.md).

Vėliau naudokite [atnaujinimo](updating.lt.md), [kopijų](../backups.lt.md), [CLI](../administration/cli.lt.md) ir [problemų sprendimo](../troubleshooting.lt.md) vadovus.
