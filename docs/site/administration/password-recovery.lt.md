---
title: KinKudos tėvų slaptažodžio atkūrimas
description: Atkurkite tėvų slaptažodį el. paštu, kai veikia SMTP, arba serverio CLI naudodami vienkartinį šeimos atkūrimo kodą.
---

# Tėvų slaptažodžio atkūrimas

## Atkūrimas el. paštu

Kai SMTP įjungtas, tėvų prisijungimo puslapyje pasirinkite **Pamiršote slaptažodį?**, įrašykite aktyvios paskyros el. pašto adresą ir pasinaudokite laiško nuoroda. Prieš manydami, kad paskyros nėra, patikrinkite šlamštą ir nustatytą siuntėjo adresą.

## Atkūrimas serveryje

Jeigu el. paštas neveikia, naudokite pirmojo paruošimo metu išsaugotą vienkartinį šeimos atkūrimo kodą. Pirmiausia sukurkite kopiją, tada `deploy` kataloge interaktyviai vykdykite:

```bash
docker compose exec app python manage.py reset_parent_password --username TEVU_NAUDOTOJAS
```

`TEVU_NAUDOTOJAS` pakeiskite tiksliu prisijungimo vardu. Komanda nematomai paprašo atkūrimo kodo ir naujo slaptažodžio, taiko Django slaptažodžių taisykles, o pakeitus slaptažodį senos sesijos nebegalioja.

Neskelbkite atkūrimo kodo, nedėkite jo į komandos argumentą ir nelaikykite serveryje šalia duomenų bazės. Jei kodo neišsaugojote, naudokite atskirai kontroliuojamą [avarinio administratoriaus](emergency-admin.lt.md) procedūrą, o ne mėginkite atrakinti `/setup/`.
