---
title: Avarinio KinKudos administratoriaus sukūrimas
description: Sukurkite laikiną Django superuser tik tada, kai neveikia nė vienas įprastas KinKudos tėvų paskyros atkūrimo būdas.
---

# Sukurkite avarinį administratorių

Šį kelią naudokite tik inicializuotai šeimai nebeturint veikiančio tėvų administratoriaus ir negalint atkurti prieigos nei el. paštu, nei atkūrimo kodu. Jis iš naujo neatveria pirmojo setup ir neatkuria trūkstamų šeimos duomenų.

1. Sukurkite ir patikrinkite kopiją.
2. Serverio prieigą apribokite patikimu administratoriumi.
3. `deploy` kataloge vykdykite:

```bash
docker compose exec app python manage.py createsuperuser
```

Komanda sukuria Django superuser. KinKudos tėvų prieiga remiasi Django vartotojų paskyromis, todėl ši paskyra gali prisijungti įprastame tėvų prisijungimo puslapyje ir pasiekti esamą šeimą. Naudokite unikalų vardą, el. paštą ir stiprų slaptažodį.

Atkūrę įprastą administravimą peržiūrėkite aktyvias tėvų paskyras ir išjunkite avarinę, jei jos nebereikia. Nesidalykite ja, nenaudokite kasdien ir neviešinkite Django administravimo – Django admin kelias pagal nutylėjimą išjungtas.
