---
title: Saugus KinKudos atnaujinimas
description: Sukurkite kopiją, įdiekite patikrintą KinKudos leidimą, patikrinkite konteinerių būseną ir supraskite ribotą automatinį atvaizdo grąžinimą.
---

# Saugiai atnaujinkite KinKudos

Palaikomas tik naujausias paskelbtas leidimas. Perskaitykite jo [leidimo pastabas](https://github.com/VooZ2/kinkudos/releases), turėkite patikrintą kopiją ir niekada nepakeiskite nuolatinių `data` ar `secrets` katalogų failais iš leidimo archyvo.

## Prieš atnaujindami

1. Įsitikinkite, kad esama instaliacija veikia.
2. Patikrinkite naują nuotolinę kopiją ir laikykite saugyklos slaptažodį atskirai.
3. Patikrinkite laisvą disko vietą.
4. Užsirašykite dabartinę versiją.
5. Perskaitykite konkretaus leidimo veiksmus.

## Palaikomas atnaujinimas

Naudokite leidimo archyvo, SHA256 failo ir `install-release.sh` eigą iš [techninio diegimo aprašo](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.lt.md#esamos-instaliacijos-atnaujinimas). Komandas vykdykite diegimo šakniniame kataloge, ne atsitiktinėje Compose kopijoje.

Atnaujintojas patikrina leidimo duomenis ir kontrolinę sumą, parsiunčia ir bandomai paleidžia konkrečios versijos atvaizdą, tikrina katalogų teises, sukuria nuoseklią DB kopiją, paleidžia naują programą ir kopijų agentą, laukia sveikatos patikros, tikrina migracijas bei versiją ir atnaujina valdymo scenarijus. `.env`, `data`, įkelti failai, kopijos ir paslaptys išlieka.

Hostinger aplinkoje naudokite Docker Manager palaikomą Update veiksmą ir po jo
patikrinkite valdomą Traefik maršrutą bei HTTPS rezultatą. Prieš atnaujinimą
pirmiausia sukurkite VPS snapshot.

## Patikrinkite rezultatą

```bash
cd /opt/kinkudos/deploy
docker compose ps
docker compose logs --tail=100 app
```

Atverkite KinKudos, patikrinkite rodomą versiją, prisijunkite ir atverkite įprastą
tėvų puslapį. Hostinger aplinkoje papildomai patikrinkite Docker Manager būseną,
Traefik maršrutą, HTTPS adresą, prisijungimą ir šeimos duomenis naršyklėje.

## Jei atnaujinimas nepavyko

Naujai programai netapus sveikai, atnaujintojas mėgina grąžinti ankstesnį atvaizdą, jei jis pasiekiamas. Tai ribotas programos atvaizdo atkūrimas, **ne** bendras duomenų bazės ar schemos rollback. Neperrašykite naujesnės gyvos DB senesne kopija. Išsaugokite klaidos tekstą ir naudokite [problemų sprendimo vadovą](../troubleshooting.lt.md).
