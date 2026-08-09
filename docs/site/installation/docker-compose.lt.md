---
title: KinKudos diegimas su Docker Compose
description: Įdiekite KinKudos naudodami oficialias Compose paslaugas, nuolatinius serverio katalogus, sugeneruotas paslaptis ir turimą HTTPS atvirkštinį tarpinį serverį.
---

# Diegimas su Docker Compose

Šis kelias skirtas patyrusiems savarankiško diegimo naudotojams, integruojantiems KinKudos į turimą Linux, NAS, Docker ar atvirkštinio tarpinio serverio (proxy) aplinką. Naudokite konkretaus leidimo `deploy/` failus; nekopijuokite pavienės Compose ištraukos be jai reikalingų paslapčių, scenarijų ir proxy papildinio.

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

## Rankinis Docker Compose diegimas

Parsisiųskite konkretaus GitHub leidimo archyvą ir SHA256 failą, juos
patikrinkite, tada naudokite leidimo `deploy/compose.yml` kartu su atitinkamu
proxy papildiniu. Oficialūs failai prižiūrimi [deploy kataloge](https://github.com/VooZ2/kinkudos/tree/main/deploy).

Prieš paleisdami paruoškite domeną, HTTPS, tinkamai sukonfigūruotą atvirkštinį
tarpinį serverį ir nuolatinius `data/`, `backups/`, `backup-state/` bei
`secrets/` katalogus. Palaikomi `host`, `traefik` ir `container` papildiniai iš
`deploy/`.

Compose failas tikisi, kad šie serverio paslapčių failai jau egzistuoja; Docker
Compose jų nesugeneruoja:

```text
secrets/django_secret_key
secrets/setup_token
secrets/vapid_private.pem
secrets/vapid_public.txt
secrets/smtp_password       # gali būti tuščias, kai SMTP išjungtas
secrets/restic_password
secrets/backup_agent_token
```

Kopijų agentas taip pat prijungia `secrets/backup/` katalogą. Paruošimo scenarijus
sukuria šį katalogą ir tuščią `restic.env` šabloną; jį sukonfigūruokite, kai
įjungsite nuotolines kopijas.

Nepaleiskite paprastos Compose komandos tuščioje diegimo šaknyje. Docker
įspės apie trūkstamus paslapčių failus ir vėliau gali baigti darbą klaida,
pavyzdžiui, `invalid mount config ... secrets/restic_password`. Naujame
bendrajame serveryje rinkitės [vedamąjį serverio diegiklį](guided-installer.lt.md).
Rankiniam patikrinto leidimo diegimui pirmiausia ne root naudotoju iš diegimo
katalogo paleiskite `./bootstrap.sh`; jis sukuria šiuos failus, nuolatinius
katalogus ir pasirinktą proxy papildinį, tada paleidžia paslaugas.

Nuspėjamam diegimui `compose.yml` palikite konkrečios versijos atvaizdą:

```yaml
image: vooz2/kinkudos:<version>
```

Kataloge, kuriame yra sukonfigūruotas `compose.yaml` (arba nukopijuoti leidimo
Compose failai), paleiskite:

```bash
docker compose up -d --pull always
```

Komanda parsiunčia pasirinktą atvaizdą, paleidžia programą ir kopijų agentą,
o nuolatinius duomenis palieka serverio kataloguose. `latest` galima naudoti
tik sąmoningai pasirinkus visada sekti naujausią stabilią versiją; nuspėjamam
diegimui rekomenduojama konkreti versijos žyma.

Jei naujam paruoštam serveriui norite interaktyvios eigos, rinkitės [vedamąjį
serverio diegiklį](guided-installer.lt.md). Paleidę Compose atverkite savo HTTPS
adresą ir tęskite [pradinį nustatymą naršyklėje](first-time-setup.lt.md).

## Nuolatiniai duomenys ir paslaptys

Kurkite viso `data/` katalogo atsargines kopijas: jame yra ir `kinkudos.sqlite3`, ir privačios įkeltos nuotraukos kataloge `data/media/`. Jei naudojate nuotolines atsargines kopijas, atskirai apsaugokite `secrets/restic_password` ir `secrets/backup/restic.env` — juose yra slaptažodis ir saugyklos nustatymai, reikalingi toms kopijoms pasiekti. Niekada nekelkite `.env`, `secrets`, duomenų bazių, atsarginių kopijų ar įkeltų failų į Git. Konteinerio pašalinimas ar perkūrimas neturi pašalinti šių serverio katalogų. Palaikoma eiga aprašyta [atsarginių kopijų ir atkūrimo vadove](../backups.lt.md).

Vėliau naudokite [atnaujinimo](updating.lt.md), [kopijų](../backups.lt.md), [CLI](../administration/cli.lt.md) ir [problemų sprendimo](../troubleshooting.lt.md) vadovus.
