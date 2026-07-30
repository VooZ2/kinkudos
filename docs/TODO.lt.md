# KinKudos darbų sąrašas

Čia paliekami tik neatlikti rankiniai patikrinimai, sąmoningai atidėti darbai
ir naujai aptiktos problemos. Užbaigti leidimų pakeitimai aprašomi
`CHANGELOG.lt.md`.

## 26.0.0 likusios rankinės patikros

- [ ] Švariai įdiegti leidimą ARM64 „Orange Pi“ serveryje ir patikrinti
  interaktyvius kalbos, domeno, tinklų, šeimos, pirmo tėvo ir vaikų profilių
  klausimus.
- [ ] Atnaujinti esamą 0.13.0 instaliaciją į 26.0.0 ir patvirtinti, kad duomenų bazė,
  nuotraukos, `.env`, SMTP, VAPID ir esami `restic` duomenys išliko.
- [ ] Su tikra ribotų teisių „Backblaze B2“ programos rakto pora patikrinti
  atskirą testinį bucket, saugyklos išsaugojimą, automatinę ir rankinę kopiją,
  oranžinę nenustatytos saugyklos, raudoną pasenusios kopijos, žalią
  tvarkingos kopijos būseną ir kopijos vientisumo patikrą.
- [ ] Atskirame bandymų kataloge atlikti dokumentuotą DB ir nuotraukų atkūrimą
  iš `restic` kopijos. Produkcijos duomenų neatkurti bandymo metu.
- [ ] Patikrinti „Robliux Pasaulio“ temą LT ir EN kalbomis kompiuteryje,
  „iPhone Safari“, įdiegtoje iOS PWA, „iPad“ ir „Android“ naršyklėje:
  kontrastą, mygtukų paspaudimą, dialogus, konfeti, garsą ir valiutos formas.

## Ankstesni likę įrenginių patikrinimai

- [ ] Patikrinti vienodą tėvų skilčių tarpą ir poraštę kompiuteryje,
  „iPhone Safari“, įdiegtoje PWA ir „Android“ naršyklėje.
- [ ] Patikrinti vaiko išvaizdos kortelę, temos automatinio keitimo žymimąjį
  laukelį ir pagalbinių tekstų tipografiką visose septyniose temose telefone,
  planšetėje ir kompiuteryje.
- [ ] Patikrinti darbų paiešką, tėvų atsakymo kortelę ir atsiliepimo veiksmų
  eilutę „iPhone“, „iPad“ bei kompiuterio naršyklėje.
- [ ] Dviejose vaiko sesijose patikrinti automatinį balanso, darbo ir prizo
  sprendimų atsinaujinimą be rankinio puslapio perkrovimo.

## Atidėta

- [ ] Prieš repozitoriją padarant viešą, nuspręsti, ar perrašyti ankstesnių
  commitų ir `v0.12.4` žymos istoriją, kurioje dar galima rasti pašalintus
  šeimai būdingus testų vardus ir seną šeimos pavadinimo pavyzdį.
- [ ] Papildomus „Azure Blob“, „Google Cloud Storage“ ir „rclone“ tiekėjus
  pridėti tik paruošus atskiras saugaus autentifikavimo bei atkūrimo patikras.
