---
title: KinKudos CLI komandų atmintinė
description: Naudokite patikrintas KinKudos Docker Compose komandas būsenai, žurnalams, patikroms, priežiūrai, kopijoms, slaptažodžio atkūrimui ir avarinei prieigai.
---

# CLI komandų atmintinė

Šias komandas vykdykite tik tinkamame `deploy` kataloge. Prieš paskyrų atkūrimą ar kitą jautrų veiksmą sukurkite kopiją.

| Paskirtis | Komanda |
|---|---|
| Būsena | `docker compose ps` |
| Programos žurnalai | `docker compose logs --tail=100 app` |
| Kopijų žurnalai | `docker compose logs --tail=100 backup-agent` |
| Django diegimo patikra | `docker compose exec -T app python manage.py check --deploy` |
| Priežiūra | `docker compose exec -T app python manage.py run_maintenance` |
| Suėjusių loterijos priminimų, paskirtų darbų priminimų ir išsaugotų rinkinių siuntimas | `docker compose exec -T app python manage.py send_lottery_reminders` |
| Užblokavusio tinklo ribojimo išjungimas | `docker compose exec -T app python manage.py disable_network_restrictions` |
| Nustatytos nuotolinės kopijos paleidimas | `./backup.sh` |
| Tėvų slaptažodžio atkūrimas | `docker compose exec app python manage.py reset_parent_password --username TEVU_NAUDOTOJAS` |
| Avarinė paskyra | `docker compose exec app python manage.py createsuperuser` |

Neinteraktyvioms komandoms naudokite `-T`. Slaptažodžio ar paskyros komandoms, kurioms reikia terminalo įvesties, jo nenaudokite. Įprastam administravimui nenaudokite Django `shell` ir tiesiogiai neredaguokite apskaitos, šeimos ar paskyrų įrašų.

`send_lottery_reminders` yra tas pats maždaug 30 minučių laikmatis, naudojamas pasirenkamiems nutrinamų bilietų priminimams. Jis taip pat nusiunčia švelnų priminimą vaikui, kai paskirtų darbų rinkinys vis dar laukia apie tris valandas po išsiuntimo, ir kartą per sutampančią vietinę dieną paleidžia suėjusius išsaugotus rinkinius.

Senoji `setup_family` komanda lieka suderinamumo ir pažangiu keliu, bet nėra palaikomas pirmojo paruošimo būdas. Naujos instaliacijos naudoja naršyklės `/setup/`.
