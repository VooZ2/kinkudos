---
title: KinKudos sustabdymas arba pašalinimas
description: Sustabdykite KinKudos konteinerius netyčia neištrindami šeimos duomenų, paslapčių, kopijų ar nuolatinių volume.
---

# Sustabdykite arba pašalinkite KinKudos

Konteinerių sustabdymas ir šeimos duomenų ištrynimas yra skirtingi veiksmai. Prieš abu sukurkite ir patikrinkite kopiją.

Hostinger Docker Manager programai naudokite Docker Manager sustabdymo arba
pašalinimo veiksmą, neištrindami `kinkudos-data` named volume. Tai pašalina
konteinerius, bet išsaugo programos duomenų bazę, mediją ir vykdymo paslaptis.
Jei reikia programą sukurti iš naujo, importuokite tą patį Compose aprašą.

Bendrame diegime jo `deploy` kataloge naudokite `docker compose down`. Nepridėkite `-v`, kol savarankiškai nenustatėte kiekvieno volume ir sąmoningai nenorite jo sunaikinti.

Visam laikui pašalinti `/opt/kinkudos`, prijungtus duomenis, paslaptis, kopijas ar Docker volumes yra negrįžtama. Ši instrukcija tokių komandų neteikia. Pirmiausia tiksliai nustatykite kelius; nenaudokite plataus rekursinio trynimo ar neišskleistų kintamųjų.
