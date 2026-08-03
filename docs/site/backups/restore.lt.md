---
title: KinKudos atkūrimas iš atsarginės kopijos
description: Paruoškite atskirą KinKudos restore bandymą ir sužinokite, kodėl gyvos instaliacijos komandos neskelbiamos iki pilno release atkūrimo bandymo.
---

# Atkurkite KinKudos iš kopijos

Restore yra serverio administratoriaus veiksmas, galintis sunaikinti naujesnius šeimos duomenis. Šiame leidime nėra Web UI restore mygtuko ar palaikomos vienos komandos automatinės procedūros.

Prieš atkurdami išsaugokite dabartinį serverį, nustatykite tikslią KinKudos versiją, pasirūpinkite restic saugyklos slaptažodžiu ir reikalingomis paslaptimis bei sukurkite papildomą dabartinio `data` katalogo kopiją. Pirmą atkūrimą atlikite tik izoliuotame bandymų kataloge ar laikiname testiniame VPS.

Atkūrimo bandymas užbaigtas tik patikrinus, kad:

- SQLite DB praeina vientisumo patikrą;
- privati medija yra ir atsidaro;
- tėvų bei susietų vaikų prieiga veikia kaip tikėtasi;
- atkurta programos versija ir migracijos suderinamos;
- `app` tampa sveikas;
- naują kopiją galima paleisti neperrašant bandymo šaltinio.

Tikslios gyvos instaliacijos pakeitimo komandos sąmoningai neskelbiamos, kol visa eiga nepatikrinta su paskelbtu KinKudos archyvu ir nuotoliniu snapshot. Nenaudokite bendrų restic komandų produkciniame šeimos serveryje.
