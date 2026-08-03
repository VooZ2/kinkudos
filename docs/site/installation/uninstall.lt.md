---
title: KinKudos sustabdymas arba pašalinimas
description: Sustabdykite KinKudos konteinerius netyčia neištrindami šeimos duomenų, paslapčių, kopijų ar Caddy sertifikatų.
---

# Sustabdykite arba pašalinkite KinKudos

Konteinerių sustabdymas ir šeimos duomenų ištrynimas yra skirtingi veiksmai. Prieš abu sukurkite ir patikrinkite kopiją.

Atpažintai Hostinger instaliacijai kaip root vykdykite:

```bash
/opt/kinkudos/deploy/uninstall-hostinger.sh /opt/kinkudos
```

Scenarijus įvykdo `docker compose down`: pašalina konteinerius, bet sąmoningai išsaugo programos duomenis, paslaptis, kopijas, diegimo failus ir Caddy sertifikatų volumes. Dar kartą paleidus palaikomą Hostinger installerį ši atpažinta instaliacija tęsiama.

Bendrame diegime jo `deploy` kataloge naudokite `docker compose down`. Nepridėkite `-v`, kol savarankiškai nenustatėte kiekvieno volume ir sąmoningai nenorite jo sunaikinti.

Visam laikui pašalinti `/opt/kinkudos`, prijungtus duomenis, paslaptis, kopijas ar Docker volumes yra negrįžtama. Ši instrukcija tokių komandų neteikia. Pirmiausia tiksliai nustatykite kelius; nenaudokite plataus rekursinio trynimo ar neišskleistų kintamųjų.
