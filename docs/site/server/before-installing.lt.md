# Prieš diegiant KinKudos

Šis vadovas skirtas žmogui, kuris prižiūrės šeimos serverį. KinKudos nėra
hostuojama paslauga: serverio administratorius atsako už serverį, HTTPS,
prisijungimo duomenis, atnaujinimus ir atkūrimą.

> **Kam:** Serverio administratoriui<br>
> **Sudėtingumas:** Linux ir Docker administravimas<br>
> **Rezultatas:** Paruoštas ir saugus diegimo pradžios taškas

## Ko reikia prieš diegiklį

- 64 bitų ARM arba x86 Linux serverio ir administratoriaus paskyros su `sudo`;
- Docker Engine bei Docker Compose papildinio;
- į šį serverį nukreipto hosto vardo;
- HTTPS reverse proxy, pavyzdžiui, Caddy, Nginx, Nginx Proxy Manager, Traefik
  ar lygiaverčio sprendimo; ir
- prieigos prie KinKudos leidimo archyvo, jo SHA256 kontrolinės sumos ir
  viešo Docker atvaizdo.

Oficialus procesoriaus, atminties ar disko minimumas nenustatytas. Serverį
parinkite pagal šeimos duomenų bazę, įkeltas nuotraukas, kopijų procesą,
operacinę sistemą ir atnaujinimams reikalingą rezervą. Neatidarykite KinKudos
programos prievado tiesiogiai į internetą; viešą HTTPS turi užbaigti reverse
proxy.

## Palaikomi diegimo keliai

| Situacija | Būsena |
| --- | --- |
| Naujas 64 bitų Linux serveris su Docker Compose ir palaikomu HTTPS proxy | Aprašytas diegimo kelias. |
| Serveryje veikiantis Caddy arba Nginx | Aprašytas reverse proxy režimas. |
| Konteinerinis proxy arba Traefik | Aprašytas reverse proxy režimas. |
| Kitos Linux distribucijos, NAS produktai, nestandartiniai proxy ar tinklai | Gali veikti, bet palaikoma tik bendruomenės galimybių ribose. |

Keisdami tinklo ar proxy nustatymus išlaikykite atidarytą esamą SSH sesiją.
Prieš tikėdamiesi HTTPS sertifikato patikrinkite, kad DNS pasiekia serverį.

## Toliau

Paleiskite [paruošto Docker serverio diegiklį](../start/quick-install.lt.md),
tada prieš nestandartinius pakeitimus perskaitykite visą [diegimo
vadovą](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.lt.md).

[English](before-installing.md)
