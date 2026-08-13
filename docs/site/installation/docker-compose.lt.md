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

Standartiniame Compose diegime `app` naudoja vidinį programos ir kopijų agento
tinklą bei atskirą neviešą egress tinklą DNS, HTTPS, SMTP ir „Web Push“ ryšiui.
`backup-agent` vidinį valdymo tinklą laiko atskirai nuo savo išorinio ryšio ir
neturi viešo kopijų prievado. `host` režimu vienintelė programos publikacija
serveryje yra lokali jungtis `127.0.0.1:8000`; jos negalima pakeisti į
`0.0.0.0:8000`.

## Prieš diegiklį pasirinkite proxy režimą

`bootstrap.sh` paraginimas neįdiegia ir nesukonfigūruoja atvirkštinio tarpinio
serverio (proxy). Jis tik parenka Compose papildinį pagal jau paruoštą proxy.
Režimą rinkitės pagal tai, kas jau veikia serveryje:

| Paraginimo pasirinkimas | Kada rinktis | Kas turi būti paruošta |
|---|---|---|
| `host` | Caddy arba Nginx veikia tiesiogiai VPS serveryje | Proxy svetainė jūsų domenui, DNS įrašas į VPS ir vieši 80/443 prievadai |
| `traefik` | Traefik veikia kaip Docker paslauga | Išorinis Traefik tinklas, pagal nutylėjimą `web`, ir veikiantis sertifikatų resolveris |
| `container` | Nginx Proxy Manager ar kitas proxy veikia Docker konteineryje | Išorinis proxy tinklas, pagal nutylėjimą `proxy`, ir maršrutas į `app` servisą per `8000` prievadą |

Domeno paraginime įrašykite tik domeną, be `https://` ir be pasvirojo brūkšnio
pabaigoje. Proxy režimo paraginimas priima tik `host`, `traefik` arba
`container`. Šie pasirinkimai aprašo tinklo ryšį, o ne terminalo komandas.

Pasirinkę `host`, proxy upstream paruoškite prieš paleisdami KinKudos. Minimalus
„Caddy“ aprašas:

```caddyfile
family.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

`family.example.com` pakeiskite domenu, kurį įvedėte diegimo metu. Naudodami
Nginx nukreipkite svetainę į `http://127.0.0.1:8000` ir perduokite `Host`,
`X-Forwarded-Proto` bei `X-Forwarded-For` antraštes. Prieš tikėdamiesi viešo
HTTPS patikrinkite konfigūraciją ir perkraukite proxy, pavyzdžiui:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Naudodami Nginx vietoje to vykdykite `sudo nginx -t` ir `sudo systemctl reload nginx`.

Naudodami `traefik` arba `container`, kintamąjį `KINKUDOS_PROXY_NETWORK`
nustatykite į tikslų jau egzistuojančio Docker tinklo pavadinimą, jei jis nėra
numatytasis. Pavyzdžiui:

```bash
KINKUDOS_PROXY_NETWORK=traefik-public ./bootstrap.sh
```

`traefik` rinkitės tik tada, kai Traefik prijungtas prie šio tinklo. `container`
rinksitės tik tada, kai kitas proxy prijungtas prie jo ir nukreiptas į KinKudos
`app` servisą per `8000` prievadą.

Vedamasis paruošimas `KINKUDOS_TRUSTED_PROXIES` įrašo pagal pasirinktą proxy
režimą: `host` – loopback, o `traefik` ar `container` – Docker proxy tinklo
CIDR. Esama netuščia reikšmė paliekama. Pakartotinai paleidus `bootstrap.sh`
išlieka esamas proxy režimas, tinklas, papildinys ir aiškiai nustatyta
patikimų proxy reikšmė; Traefik ar konteinerinio proxy papildinys
neperjungiamas į `host`. Hostinger Compose palieka savą privatų Docker tinklo
atsarginį variantą ir šio pagalbinio scenarijaus nenaudoja. Niekada
nepasitikėkite visu internetu.

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

Kataloge, kuriame yra sukonfigūruotas `compose.yml` (arba nukopijuoti leidimo
Compose failai), paleiskite:

```bash
docker compose up -d --pull always
```

Komanda parsiunčia pasirinktą atvaizdą, paleidžia programą ir kopijų agentą,
o nuolatinius duomenis palieka serverio kataloguose. `latest` galima naudoti
tik sąmoningai pasirinkus visada sekti naujausią stabilią versiją; nuspėjamam
diegimui rekomenduojama konkreti versijos žyma.

Prieš atverdami svetainę patikrinkite rezultatą:

```bash
docker compose ps
```

Palaukite, kol `app` būsena taps `healthy`. Jei taip neįvyksta, peržiūrėkite
`docker compose logs --tail=100 app` ir nekartokite naujo diegimo vedlio esamame
diegime.

Jei naujam paruoštam serveriui norite interaktyvios eigos, rinkitės [vedamąjį
serverio diegiklį](guided-installer.lt.md). Paleidę Compose atverkite savo HTTPS
adresą ir tęskite [pradinį nustatymą naršyklėje](first-time-setup.lt.md).

## Nuolatiniai duomenys ir paslaptys

Kurkite viso `data/` katalogo atsargines kopijas: jame yra ir `kinkudos.sqlite3`, ir privačios įkeltos nuotraukos kataloge `data/media/`. Jei naudojate nuotolines atsargines kopijas, atskirai apsaugokite `secrets/restic_password` ir `secrets/backup/restic.env` — juose yra slaptažodis ir saugyklos nustatymai, reikalingi toms kopijoms pasiekti. Niekada nekelkite `.env`, `secrets`, duomenų bazių, atsarginių kopijų ar įkeltų failų į Git. Konteinerio pašalinimas ar perkūrimas neturi pašalinti šių serverio katalogų. Palaikoma eiga aprašyta [atsarginių kopijų ir atkūrimo vadove](../backups.lt.md).

Vėliau naudokite [atnaujinimo](updating.lt.md), [kopijų](../backups.lt.md), [CLI](../administration/cli.lt.md) ir [problemų sprendimo](../troubleshooting.lt.md) vadovus.
