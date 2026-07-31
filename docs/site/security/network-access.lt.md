# Tinklo prieiga

Tinklo prieiga yra pasirenkamas, tik administratoriui skirtas IP leidžiamų adresų sąrašas. Jis papildo tėvų slaptažodžius, vaikų PIN, įrenginių susiejimą ir bandymų ribojimą, bet jų nepakeičia.

Jis naudingiausias stabiliam namų tinklui ar VPN. Jo nereikia šeimai, kurios IP dažnai keičiasi arba kuri dažnai naudoja mobilųjį internetą ne namuose.

| Režimas | Poveikis |
| --- | --- |
| **Prieiga iš interneto** | Jokie IP neblokuojami – įprastas numatytas režimas. |
| **Riboti vaikų prieigą** | Vaikų puslapiai veikia tik iš įrašytų adresų ar tinklų; tėvų puslapiai lieka pasiekiami. |
| **Riboti visą prieigą** | Vaikų ir tėvų puslapiai veikia tik iš įrašytų adresų. |

## Prieš išsaugant taisyklę

1. Formoje patikrinkite rodomą **Dabartinį IP adresą**.
2. Įveskite po vieną IP ar CIDR tinklą eilutėje, pvz. `192.0.2.25`, `192.0.2.0/24` arba `2001:db8::/64`.
3. Rinkdamiesi **Riboti visą prieigą**, būtinai įtraukite dabartinį IP – KinKudos kitaip neleis išsaugoti.
4. Kol nepatikrinote tėvų ir vaiko įrenginio, turėkite serverio administratorių su SSH ar konsolės prieiga.

> Nespėliokite tinklo diapazono. Netinkama visos prieigos taisyklė gali užrakinti visus tėvus ir vaikus, o ribojimą tada išjungs tik serverio administratorius dokumentuota avarine komanda.

Taisyklės keitimui reikia administratoriaus dabartinio slaptažodžio ir veiksmas įrašomas į saugumo istoriją.

[Tėvų nustatymai →](../parents/settings.lt.md) · [PIN ir prisijungimo apsauga →](pin-and-sign-in.lt.md) · [English](network-access.md)
