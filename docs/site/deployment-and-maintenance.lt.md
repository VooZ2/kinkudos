# Serverio administravimas

Ši skiltis skirta žmogui, kuris prižiūri šeimos KinKudos serverį. Kasdieniams
tėvams paprastai reikia tik programos. Nekeiskite tinklo ribojimų, nuotolinių
kopijų duomenų ar serverio konfigūracijos, jeigu nesuprantate pasekmės ir
negalite atkurti prieigos.

<div class="grid cards" markdown>

-   :material-shield-check-outline: **Prieš diegiant**

    ---

    Reikalavimai, palaikomi keliai, HTTPS ir atsakomybės, kurias šeima prisiima
    diegdama savarankiškai.

    [Paruošti serverį →](server/before-installing.lt.md)

-   :material-download-outline: **Diegti paruoštame serveryje**

    ---

    Vedamą diegiklį naudokite tik naujai KinKudos instaliacijai.

    [Atidaryti greitą diegimą →](start/quick-install.lt.md)

-   :material-sync: **Atnaujinti ir atkurti**

    ---

    Naudokite naujausią leidimą, saugokite kopijas, išbandykite atkūrimą ir
    diagnozuokite problemą neatskleisdami šeimos duomenų.

    [Atidaryti atnaujinimo ir atkūrimo vadovą →](server/updates-and-recovery.lt.md)

-   :material-book-open-page-variant-outline: **Išsamus diegimo vadovas**

    ---

    Tikslios Docker, Ubuntu, Caddy/Nginx/Traefik, atnaujinimo ir diagnostikos
    komandos laikomos kartu su leidimo šaltiniu.

    [Atidaryti diegimo vadovą ↗](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.lt.md)

</div>

## Serverio atsakomybės trumpai

| Sritis | Ką turi nuspręsti arba prižiūrėti administratorius |
| --- | --- |
| **Domenas ir HTTPS** | DNS nukreipimą, sertifikatą galintį gauti reverse proxy ir saugią viešą prieigą. |
| **Docker ir atnaujinimai** | Naujausią leidimą, konteinerių sveikatą ir serverio priežiūrą. |
| **El. paštas** | Pasirenkamus SMTP duomenis slaptažodžio atkūrimui ir atsiliepimų pranešimams. |
| **Tinklo prieiga** | Pasirenkamus IP leidžiamų adresų sąrašus; juos būtina atsargiai tikrinti, kad šeima neužsirakintų. |
| **Kopijos** | Nuotolinę saugyklą, saugyklos slaptažodį, naują sėkmę ir išbandytą atkūrimą. |

[Greita pagalba →](quick-help.lt.md) · [English](deployment-and-maintenance.md)
