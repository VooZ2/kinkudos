---
title: KinKudos diegimo ir serverio problemų sprendimas
description: Saugiai diagnozuokite domeno, HTTPS, pirmojo setup, prisijungimo, SMTP, atnaujinimo, konteinerių, vietos ir nuolatinių duomenų problemas.
---

# Problemų sprendimas

Pradėkite nuo konkretaus simptomo. Pirmu veiksmu netrinkite konteinerių, volumes, `data` ar `secrets`.

## KinKudos neatsidaro

**Galimos priežastys:** DNS rodo kitur, užblokuoti 80/443 prievadai, sustojęs proxy arba nesveikas `app`.

**Patikrinkite:**

```bash
getent hosts seima.example.com
cd /opt/kinkudos/deploy
docker compose ps
```

Hostinger profilyje vykdykite `/opt/kinkudos/deploy/hostinger-healthcheck.sh /opt/kinkudos`. Pataisykite DNS ar firewall ir tikrinkite dar kartą. Neviešinkite `8000`.

## Domenas arba HTTPS dar neveikia

Hostinger patikra rodo **deployed but HTTPS pending**, kai KinKudos ir Caddy veikia, bet sertifikatas dar neparuoštas. Įsitikinkite, kad domenas rodo į šį VPS, įeinantys TCP 80 ir 443 leidžiami ir jų neužėmė kita paslauga. Palaukite DNS atsinaujinimo ir pakartokite patikrą.

Neapeikite sertifikato įspėjimų ir nepradėkite įprastai naudoti šeimos programos per viešą HTTP.

## Diegiklis nepasileidžia

Hostinger diegikliui reikia root, Hostinger Ubuntu 24.04 Docker šablono, veikiančio Docker, bent Compose 2.20, Docker 24 ir įprastų sistemos įrankių. Vadovaukitės tikslia jo klaida, o ne diekite atsitiktinius paketus ar išjunkite patikras.

Bendras vedamasis diegiklis turi kitus reikalavimus: ne root diegimo naudotoją ir jau veikiantį HTTPS proxy. Nemaišykite abiejų profilių viename diegimo kataloge.

## Setup puslapis nerodomas

`/setup/` pasiekiamas tik kai nėra Django vartotojo ar vaiko ir šeimos setup nepažymėtas užbaigtu. Neužbaigta instaliacija ten nukreipia ir iš įprastų puslapių.

Jeigu nukreipiama į tėvų prisijungimą ar skydelį, setup jau užbaigtas arba migracijos pažymėtas užbaigtu. Nebandykite jo atrakinti. Esamai šeimai naudokite [slaptažodžio atkūrimą](administration/password-recovery.lt.md).

## Setup kodas nepriimamas

Nukopijuokite dabartinį diegiklio parodytą kodą be papildomų tarpų. Hostinger profilyje iki sėkmingos setup pabaigos jis taip pat laikomas `/opt/kinkudos/secrets/setup_token`. Tai paslaptis – nedėkite jos į nuotraukas ar pagalbos užklausas.

Dar kartą paleidus atpažintą Hostinger diegiklį esamas kodas išsaugomas. Nekeiskite paslapčių failų rankiniu būdu.

## Nepavyksta prisijungti

Įsitikinkite, kad atvėrėte tėvų prisijungimą ir naudojate tikslų setup metu sukurtą vardą. Veikiant SMTP naudokite el. pašto atkūrimą, kitu atveju – [CLI atkūrimo komandą](administration/password-recovery.lt.md). Vaiko PIN veikia tik susietame vaiko įrenginyje ir nėra tėvų slaptažodis.

## Neveikia atkūrimas el. paštu

Išjungus SMTP el. pašto atkūrimas sąmoningai slepiamas. Tėvų administratoriaus **El. pašto nustatymuose** patikrinkite tiekėjo duomenis, saugos režimą, siuntėją, šlamšto katalogą ir programos žurnalus. Išsaugant SMTP ryšys patikrinamas; atskiro dokumentuoto bandomojo laiško veiksmo šiame leidime nėra.

## Po atnaujinimo sustojo konteineris

Išsaugokite atnaujintojo išvestį, tada vykdykite:

```bash
cd /opt/kinkudos/deploy
docker compose ps
docker compose logs --tail=100 app
```

Nepraėjus sveikatos patikrai atnaujintojas gali grąžinti ankstesnį programos atvaizdą, bet tai nėra bendras DB rollback. Neperrašykite gyvos DB senesne kopija. Skaitykite [atnaujinimo vadovą](installation/updating.lt.md).

## Trūksta vietos diske

Nieko netrindami patikrinkite failų sistemą ir Docker:

```bash
df -h
docker system df
```

Pirmiausia nustatykite tikslią priežastį. Saugokite `data`, `backups`, `secrets` ir Caddy sertifikatų volumes. Nežinomame serveryje nevykdykite plataus Docker prune ar rekursinio trynimo.

## Pakeitus Compose dingo duomenys

Nebedarykite pakeitimų. Naujas tuščias bind mount gali sukurti šviežios programos įspūdį, nors seni failai tebėra kitur. Užfiksuokite aktyvią Compose konfigūraciją ir mounts, išsaugokite abi vietas ir neužbaikite `/setup/` instaliacijoje, kurioje įtariate dingusius duomenis. Atkurkite tik nustatę pradinį `data` katalogą ir turėdami išbandytą planą.

## Pagalbos prašymas

GitHub Issues skirti atkuriamoms KinKudos klaidoms ir funkcijų pasiūlymams, ne bendrai VPS administravimo pagalbai. Nurodykite KinKudos versiją, lauktą ir gautą rezultatą, saugius atkūrimo žingsnius bei redaguotą žurnalo ištrauką. Niekada neskelbkite slaptažodžių, setup ar atkūrimo kodų, API raktų, `.env`, DB, kopijų, privačios šeimos informacijos, nuotraukų ar neredaguotų žurnalų.
