# Atsarginės kopijos

Tėvų administratorius gali sukonfigūruoti šifruotas kasdienes nuotolines KinKudos duomenų bazės ir įkeltų šeimos nuotraukų kopijas. Tai labai rekomenduojama, kai šeimos duomenys tampa svarbūs, tačiau reikia saugyklos tiekėjo ir atsargaus prisijungimo duomenų tvarkymo.

Kiekviena sėkminga kopija apima duomenų bazę ir įkeltus failus. Prisijungimo duomenys bei repo slaptažodis laikomi atskiruose apsaugotuose serverio failuose, nerodomi tėvų sąsajoje ir nepatenka į „GitHub“.

| Būsena | Reikšmė | Pirmas veiksmas |
| --- | --- | --- |
| **Įjungta** | Saugykla nustatyta, sėkminga kopija ne senesnė kaip 7 dienos. | Kartais patikrinkite datą ir saugiai laikykite repo slaptažodį. |
| **Kopijuojama** | Vyksta kopija. | Palaukite; vienu metu vyksta tik viena. |
| **Neįjungta** | Nuotolinė saugykla dar nenustatyta. | Sukonfigūruokite turėdami tinkamą saugyklos paskyrą. |
| **Reikia dėmesio** | Paslauga nepasiekiama, kopija pasenusi ar grąžinta klaida. | Prieš ką nors keisdami perskaitykite ir užsirašykite klaidą. |

Atidarykite **Tėvai → Nustatymai → Atsarginės kopijos → Redaguoti nustatymus**. Administratorius įveda savo dabartinį slaptažodį; KinKudos patikrina saugyklos ryšį prieš išsaugodamas. Laukeliai: tiekėjas, S3 endpoint be `https://`, tik kopijoms skirtas bucket, jei reikia regionas, ribotų teisių application key ID ir key bei jūsų paskyros slaptažodis.

**Kurti kopiją dabar** paprašo papildomos kopijos – neatkuria failų, neperrašo gyvos duomenų bazės ir neapeina šifravimo ar patikros. Atkūrimas yra serverio administratoriaus veiksmas pagal diegimo vadovą. Prieš laikant kopijas patikimomis, išbandykite atkūrimą atskiroje saugioje vietoje ir repo slaptažodį saugokite ne serveryje.

[Tėvų nustatymai →](../parents/settings.lt.md) · [Diegimas ir priežiūra →](../deployment-and-maintenance.lt.md) · [English](backups.md)
