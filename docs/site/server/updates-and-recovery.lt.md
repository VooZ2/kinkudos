# Atnaujinimai, kopijos ir atkūrimas

Serverį laikykite naujausiame paskelbtame KinKudos leidime. Atnaujinimas ir
atkūrimas yra serverio administratoriaus darbai, o ne įprasti tėvų nustatymai.

> **Kam:** Serverio administratoriui<br>
> **Reikia:** Prieigos prie diegimo katalogo, jo paslapčių ir patikrintų kopijų<br>
> **Rezultatas:** Saugi atnaujinimo ir atkūrimo eiga

## Saugiai atnaujinkite

Naudokite tikslią [esamo diegimo atnaujinimo procedūrą](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.lt.md#esamos-instaliacijos-atnaujinimas).
Ji patikrina leidimo kontrolinę sumą ir metaduomenis, sukuria gyvos duomenų
bazės kopiją, patikrina rašomų katalogų nuosavybę, išbando atvaizdą ir programą
perjungia tik po šių patikrinimų.

Atnaujinimas skirtas išsaugoti vietinę diegimo aplinką, veikiančius duomenis,
įkėlimus, kopijas ir paslaptis. Nekeiskite šių vietų rankiniu būdu leidimo
archyvu. Prieš atnaujindami perskaitykite leidimo pastabas ir turėkite žinomą
veikiančią kopiją.

## Kopijos saugo, bet nepakeičia atkūrimo bandymo

Nuotolinės šifruotos kopijos apima šeimos duomenų bazę ir įkeltą mediją. Kopijų
saugyklos slaptažodis yra atskirai saugomas serverio duomuo: laikykite jį ne
serveryje. Tik tame pačiame diske kaip programa esanti kopija neapsaugo nuo to
serverio praradimo.

Patikrinkite programoje rodomą paskutinės sėkmingos kopijos datą ir klaidą.
Prieš rizikingą pakeitimą galite sukurti papildomą kopiją, jei kopijų paslauga
sveika, bet nelaikykite „Kurti kopiją dabar“ atkūrimo procedūra.

## Atkūrimas ir serverio perkėlimas

Palaikomos atkūrimo instrukcijos yra diegimo vadove. Pirmą atkūrimą išbandykite
atskirame saugiame kataloge; gyvas šeimos diegimas negali būti pirmasis bandymas.
Be prieigos prie saugyklos reikės ir kopijų saugyklos slaptažodžio.

Perkėlimas į kitą serverį yra atkūrimo / migracijos užduotis: paruoškite tikslinį
serverį, išsaugokite reikalingas paslaptis, atkurkite išbandytus duomenis ir tik
tada patikrinkite programą bei HTTPS, prieš nukreipdami šeimos įrenginius.
Netrinkite seno serverio, kol pakaitalas nepatikrintas.

## Kai kažkas nepavyksta

Užrašykite rodomą klaidą ir surinkite susijusius, nuasmenintus konteinerių
žurnalus, tada naudokite [diegimo vadovo diagnostiką](https://github.com/VooZ2/kinkudos/blob/main/deploy/README.lt.md)
ir [greitą pagalbą](../quick-help.lt.md). Viešame Issue niekada neskelbkite
prisijungimo duomenų, duomenų bazių, kopijų, šeimos duomenų, nuotraukų ar
neredaguotų žurnalų.

[English](updates-and-recovery.md)
