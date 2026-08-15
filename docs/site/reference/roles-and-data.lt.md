# Vaidmenų, duomenų ir ribų atmintinė

Naudokite šią atmintinę, kai reikia trumpo faktinio atsakymo, o ne vedamo
veiksmų vadovo.

## Kur laikomi šeimos duomenys

| Duomenys | Vieta ir tvarkymas |
| --- | --- |
| Šeimos nustatymai, paskyros, profiliai, taškai ir istorija | KinKudos duomenų bazėje šeimos serveryje. |
| Darbo nuotraukos, avatarai ir atsiliepimų ekrano nuotraukos | Privačioje įkeltoje medijoje šeimos serveryje. |
| Taupymo tikslai ir jų įvykiai | Tikslų įrašai ir įvykių istorija šeimos duomenų bazėje; atskirai išsaugoti paskirstymai susieti su konkrečiu tikslu. |
| Paslaptys ir tiekėjų prisijungimo duomenys | Atskirai apsaugotuose serverio failuose; niekada nerodomi viešoje repozitorijoje. |
| Pasirenkamos nuotolinės kopijos | Šifruotose restic duomenų bazės ir įkeltos medijos kopijose. |

Privačioje KinKudos šeimos programoje nėra reklamų ar integruotos analitikos.
Slapukų nenaudojanti analitika naudojama tik viešoje dokumentacijoje.

## Svarbios ribos ir laiko taisyklės

| Taisyklė | Reikšmė ar elgsena |
| --- | --- |
| Vaiko įrenginio susiejimo nuoroda | Vienkartinė; baigiasi po 10 minučių. |
| Susieto įrenginio profilis | Bendra telefono, planšetės, kompiuterio arba nežinomo įrenginio kategorija, trumpas stabilus šešių simbolių ID, naršyklės aprašas ir paskutinio naudojimo laikas. 30 dienų nenaudoti įrenginiai iš nustatymų sąrašo paslepiami iki kito panaudojimo. |
| Aktyvi susieto įrenginio prieiga | Aktyviai naudojant prieigos slapukas pratęsiamas. Atšaukus įrenginį vaiko prieiga ir pranešimai iškart panaikinami. |
| Vaiko PIN | Keturi skaitmenys; profiliui pirmiausia reikia susieto įrenginio. |
| Darbo / atsiliepimo vaizdo įkėlimas | JPEG, PNG, WebP, HEIC arba HEIF iki 12 MB. |
| Avataro įkėlimas | Tie patys formatai iki 5 MB; apkerpama į kvadratą. |
| Paskirto darbo terminas | Vidurnaktis pagal serverio vietinį laiką. Tada laukiantys punktai dingsta iš šios dienos sąrašų; nebaigti punktai žurnalo įrašų nesukuria. |
| Išsaugoti paskyrimo rinkiniai | Iki penkių pavadintų rinkinių vienam vaikui. |
| Paskirto darbo priminimas | Švelnus pranešimas vaikui apie tris valandas po rinkinio, jei bent vienas punktas vis dar laukia. |
| Nutrinamų bilietų savaitė | Nuo pirmadienio iki sekmadienio. |
| Užbaigtų darbų nuotraukų saugojimas | Šeimos pasirinkimas: neribotai, 7, 30 arba 90 dienų. |
| Išspręsto atsiliepimo nuotraukų saugojimas | Šeimos pasirinkimas: neribotai, 7, 30 arba 90 dienų. |

## Taškų ir taupymo tikslų apskaita

`LedgerEntry` išlieka išleidžiamų taškų tiesos šaltiniu. Atskirai išsaugoti
tikslų paskirstymai nėra išleidžiami. Perkėlus taškus į atskirai taupomą tikslą
sukuriamas neigiamas žurnalo įrašas, o grąžinus – teigiamas išleidžiamų taškų
įrašas. Pasirinkus ar pakeitus **Dabartinį tikslą** balansas žurnale
nesikeičia. Atskirai taupomo tikslo užbaigimas sunaudoja išsaugotą paskirstymą
taškų antrą kartą nenuskaitant, o turimus taškus naudojančio tikslo užbaigimas
po tėvų patvirtinimo tikslą nuskaito vieną kartą.

## Susijusios politikos

- [Leidimų ir palaikymo politika](release-and-support-policy.lt.md)
- [Saugumo politika GitHub](https://github.com/VooZ2/kinkudos/security/policy)

[English](roles-and-data.md)
