---
title: KinKudos atsarginės kopijos ir duomenų apsauga
description: Nustatykite šifruotas nuotolines KinKudos kopijas, atskirkite jas nuo VPS snapshot, saugokite atkūrimo paslaptis ir suplanuokite saugų restore bandymą.
---

# Atsarginės kopijos ir duomenų apsauga

Patikimas kopijų planas saugo daugiau nei veikiantį konteinerį. KinKudos SQLite duomenų bazė ir privati medija laikoma nuolatiniame `data` kataloge. Serverio paslaptys ir nuotolinių kopijų saugyklos slaptažodis saugomi atskirai.

## KinKudos programos kopija

Izoliuotas `backup-agent` sukuria nuoseklią veikiančios SQLite DB kopiją, įtraukia privačią mediją ir per restic siunčia šifruotus snapshots į Backblaze B2 arba bendrą S3 suderinamą saugyklą. Pirmas tėvų administratorius ją nustato skiltyje **Nustatymai → Atsarginės kopijos**.

Naudokite atskirą bucket ir ribotų teisių raktą. `secrets/restic_password` kopiją laikykite ne serveryje – be jos šifruotų snapshots atkurti nepavyks. Kopijos vykdomos kasdien po nustatytos valandos, vietinės DB ir nuotolinės dienos kopijos laikomos 31 dieną, o sėkminga eiga apima `restic check`. Nepavykęs suplanuotas bandymas tos dienos sėkme neįrašomas: vėliau tą pačią dieną bandoma dar kartą su ribotu laukimo didėjimu, o sėkminga suplanuota kopija tą dieną nebekartojama.
Vietinės SQLite atsarginės kopijos ir KinKudos valdomi kopijų bei būsenos katalogai saugomi tik jų savininkui prieinamomis failų sistemos teisėmis.

Tėvų administratorius gali pasirinkti **Kurti kopiją dabar**, o serverio administratorius `deploy` kataloge vykdyti:

```bash
./backup.sh
```

Tikrinkite paskutinės sėkmės laiką UI ir `backup-agent` žurnalus. Žalia būsena patvirtina naują sėkmingą eigą, bet neįrodo, kad atkūrimo procedūra veikia.

## VPS kopija arba snapshot

Hostingo tiekėjo kopija ar snapshot saugo platesnį serverio sluoksnį. Ji gali padėti sugedus visam VPS, bet nepakeičia šifruotos KinKudos programos kopijos, o atkūrimas gali perrašyti visą VPS. Patikrinkite dabartines tiekėjo saugojimo, galiojimo ir atkūrimo sąlygas.

Kai įmanoma, naudokite abu sluoksnius, ypač prieš atnaujinimą.

## Atkūrimas

Restore sąmoningai nepasiekiamas Web UI. Jis gali perrašyti gyvus šeimos duomenis, jam reikia saugyklos slaptažodžio, atitinkamų paslapčių, tinkamų savininkų ir suderinamos programos versijos.

Projektas dar neskelbia vienos komandos automatinio restore. Neeksperimentuokite gyvoje instaliacijoje. Pirmiausia atkurkite snapshot atskirame bandymų kataloge ar izoliuotame testiniame serveryje, patikrinkite DB, mediją, prisijungimą, versiją ir konteinerių sveikatą, ir tik tada planuokite kontroliuojamą gyvos instaliacijos atkūrimą. Išsamus [atkūrimo puslapis](backups/restore.lt.md) nurodo patvirtintas ribas ir liks konservatyvus, kol visa eiga nepraeis release bandymo.
