# Changelog

Visi reikšmingi projekto pakeitimai dokumentuojami šiame faile.

Formatas paremtas „Keep a Changelog“, o versijoms naudojama `YY.FEATURE.FIX`
schema.

## [Unreleased]

## [26.0.0] - 2026-07-30

### Pakeista

- KinKudos tapo produkciniu leidimu ir vartotojo sąsajoje neberodomas BETA
  prierašas.
- Versijos numeruojamos pagal `YY.FEATURE.FIX`: pirmą skaičių keičia metai,
  antrą – naujas funkcionalumas, o trečią – klaidų taisymai, dizaino darbai
  arba esamo funkcionalumo plėtra.
- Atsiliepimų nustatymuose pagal nutylėjimą rodomi neišspręsti įrašai ir
  išlaikomas puslapiavimas; išspręsti įrašai lieka pasiekiami per būsenos
  filtrą.
- Kopijų nustatymuose atskirtos oranžinė nenustatytos saugyklos, raudona
  pasenusios ar klaidingos kopijos ir žalia tvarkingos kopijos būsenos.
  Tuščios techninės reikšmės pakeistos trumpais suprantamais tekstais.
- Diegimo ir atnaujinimo dokumentacija tapo neutrali repozitorijos atžvilgiu,
  atskiria KinKudos nuotolines kopijas nuo viso serverio kopijų ir patikrai
  rekomenduoja atskirą ribotų teisių bucket.

### Pataisyta

- „Traefik“ visada nurodoma programą pasiekti per išorinį `web` tinklą, kai
  programa taip pat prijungta prie vidinio kopijų tinklo.
- Su `sudo` paleistas leidimo atnaujintojas kopijų katalogams, tarnybos
  raktams ir `restic` konfigūracijai priskiria nustatytą programos UID ir GID.
- „Compose“ ir atnaujintojo regresiniai testai saugo tinklo pasirinkimo bei
  kopijų failų nuosavybės pataisas.
- Kopijų nustatymuose neberodoma `REPLACE_WITH_REPOSITORY`, o perspėjimas apie
  pavojingus nustatymų pakeitimus pateikiamas švelniai raudoname fone.

## [0.13.0 BETA] - 2026-07-30

### Pridėta

- „Robliux Pasaulis“ tapo septintąja vaiko tema: pridėta tamsi žaidimo
  sąsaja, robliukų linksniai, „Obby“ ir „Gamepass“ tekstai, paspaudžiami
  mygtukai, neoninis konfeti bei atskiras garsas lietuvių ir anglų kalbomis.
- Tėvų nustatymuose rodoma atsarginių kopijų saugykla, paskutinė sėkminga
  nuotolinė kopija, vientisumo patikra, vykdomas darbas, klaidos ir septynių
  dienų būsenos indikatorius.
- Tėvų administratorius gali patikrinti „Backblaze B2“ arba bendrinės S3
  saugyklos duomenis ir paleisti rankinę šifruotą kopiją.
- Izoliuota kasdienė kopijų tarnyba kopijuoja nuoseklią SQLite DB ir privačias
  nuotraukas, taiko 31 dienos saugojimą bei paleidžia `restic check`.
- Pridėtos LT ir EN ARM64 „Orange Pi“ diegimo, pirmos šeimos, patikros, kopijų
  ir atnaujinimo instrukcijos.

### Pakeista

- Diegimo vedlys dabar klausia kalbos, domeno, leidžiamų privačių tinklų,
  pirmo tėvo duomenų, šeimos pavadinimo bei vaikų profilių ir nenaudoja
  konkrečios instaliacijos numatytųjų reikšmių.
- Atnaujinant iš 0.12.4 išsaugomi ir atpažįstami esami bendriniai
  `restic.env` bei repozitorijos slaptažodžiai.
- TODO paliktos tik neatliktos įrenginių ir atkūrimo patikros, atidėti
  tiekėjai bei naujai aptikti darbai.

### Saugumas

- Kopijų paslaptis valdo izoliuotas konteineris be viešo prievado ir Docker
  socket; žiniatinklio programa gauna tik išvalytą būseną ir neatgauna
  išsaugotų tiekėjo paslapčių.
- Kopijų konfigūraciją ir rankinį paleidimą gali valdyti tik pirmasis tėvų
  administratorius, keičiant prisijungimus dar kartą tikrinamas slaptažodis,
  o audite paslaptys nesaugomos.
- Iš dabartinio repozitorijos medžio pašalinti šeimai būdingi vardai ir
  konkrečios instaliacijos diagnostikos naudotojas; demo bei testų duomenys
  tapo bendriniai.

## [0.12.4 BETA] - 2026-07-30

### Pakeista

- Vaiko veiksmų žurnale dabar rodomi tik penki naujausi veiksmai.
- Dovanų pranešimuose naudojamas trumpesnis tekstas ir gavėjo temos taškų
  pavadinimas, o padovanotas kiekis pranešimo tekste neberodomas.
- Prizų, bausmių ir darbų kūrimo bei redagavimo formose emoji laukas visur
  vadinamas „Ikona“.
- Projekto README atnaujintas pagal dabartines BETA funkcijas, diegimo modelį,
  palaikomas platformas ir papildytas AI projekto atsakomybės apribojimu.

### Pataisyta

- Kalbos valdiklyje palikta tik vėliava kompaktiškame 44 px apskritame rėmelyje;
  pašalinti „LT“ / „EN“ užrašai ir „iPad“ kreivai rodoma rodyklė.
- Pranešimų valdiklyje paliktas tik varpelis tokiame pačiame 44 px rėmelyje
  kaip atsijungimo mygtukas, išlaikant prieinamą būsenos tekstą.
- Leidimų archyvai kuriami tik iš Git sekamų failų, todėl į juos negali netyčia
  patekti ignoruojamos vietinės talpyklos ar konfigūracija.

## [0.12.2 BETA] - 2026-07-29

### Pridėta

- Darbų paieška dabar filtruoja ir siūlo rezultatus iškart įvedus pirmą
  raidę; pasirinkimą galima patvirtinti klavišu „Enter“ arba palietimu.
- Vaikas gali įjungti kasdienį atsitiktinį temos keitimą. Tema pakeičiama
  naktinės priežiūros metu ne dažniau kaip kartą per dieną.

### Pataisyta

- Atmestas darbas vaikui rodomas aiškiame tėvų atsakymo bloke, kurį galima
  patvirtinti mygtuku „Supratau“, todėl senas atsakymas nebelieka pakibęs.
- Vaiko istorijoje darbams, prizams ir dovanoms rodomos tikros priskirtos
  piktogramos, o pranešimuose taisyklingai linksniuojami taškai ir teminės
  valiutos.
- Temos ir avataro valdymas sujungtas į vieną išvaizdos kortelę, suvienodinti
  pagalbiniai šriftai ir patikslinti lietuviški tekstai.
- Atsiliepimo ekrano nuotrauka atidaroma kompaktiška foto piktograma
  neišderinant būsenos valdiklių.
- Tėvų puslapių versijos poraštė telefone nebeslepiama po apatine navigacija,
  o visuose tėvų puslapiuose išlaikomas vienodas tarpas iki turinio.

## [0.12.1 BETA] - 2026-07-29

### Pridėta

- Vaikų balansas, darbų ir prizų sprendimai atsinaujina automatiškai: matomas
  puslapis tikrina mažą nekešuojamą būsenos endpointą, tikrina iškart grįžus į
  programą ar gavus push įvykį ir neperkrauna atidaryto dialogo ar pildomos
  formos.
- Pirmą gimimo datą vaikas gali įrašyti iškart, tačiau vėlesnį pakeitimą turi
  patvirtinti tėvai. Vienu metu leidžiamas tik vienas laukiantis pakeitimas, o
  tėvų atlikti pakeitimai išsaugomi audito įraše.
- Tėvų ir vaikų veiksmų istorijoje rodoma, kuri tėvų paskyra patvirtino arba
  atmetė darbą ar prizo prašymą.

### Pataisyta

- Prisijungusio vartotojo antraštėje naudojamas „KinKudos“ logotipas, paliktos
  kompaktiškos atsijungimo piktogramos, nebekartojamas šeimos pavadinimas ir
  versija. Projekto pavadinimas bei versija vienodai rodomi poraštėje.
- Nustatymų kortelė pervadinta į „Projekto nustatymai“.
- Atsiliepimai pagal nutylėjimą suskleisti ir rodo trumpą santrauką.
  Išspręstas įrašas pažymimas žaliu „Išspręsta“, o neišspręstas pasiūlymas –
  violetiniu tipo ženkleliu; pakeitus būseną išsaugomi filtrai ir puslapis.
- Net ir patvirtinus gimimo datos pakeitimą, gimtadienio dovana tam pačiam
  vaikui per kalendorinius metus gali būti paskirta tik vieną kartą.

## [0.12.0 BETA] - 2026-07-29

### Pridėta

- Vaikai gali iškart filtruoti darbų katalogą pagal pavadinimą.
- Vaikai gali saugiai dovanoti jau uždirbtus taškus kitam aktyviam šeimos
  vaikui. Abi atominio pervedimo pusės rodomos veiksmų istorijoje, o pranešimus
  įjungęs gavėjas gauna tik jam skirtą push pranešimą.
- Vaikas gali įrašyti gimimo datą, o tėvai – nustatyti kasmetinės gimtadienio
  dovanos taškus. Naktinė priežiūra juos paskiria tik kartą per kalendorinius
  metus; vasario 29-osios gimtadienis nekeliamaisiais metais minimas vasario 28 d.
- Pridėtos trys vaikų temos – „Superherojų būstinė“, „Dizaino studija“ ir
  „Pandos pasaulis“ – su savomis valiutomis, navigacija, veiksmų tekstais,
  spalvomis, efektais ir garsais lietuvių bei anglų kalbomis.

### Pataisyta

- Patikslinti lietuviški tuščio prašymų sąrašo ir darbų nuotraukų saugojimo
  tekstai.
- Filtruojant ar puslapiuojant tėvų veiksmų istoriją liekama istorijos skiltyje.
- Leidimo patikra prieš Docker atvaizdo kūrimą aptinka tuščias, sugadintas ar
  `Migration` klasės neturinčias migracijas.
- Docker atvaizdo kūrimas prieš Django migracijų įkėlimą pašalina senus Python
  bytecode failus, todėl jie nebegali užgožti teisingo migracijos šaltinio.
- Atnaujinimai diegiami iš vieno patikrinto leidimo archyvo į atskirą versijos
  katalogą. Serveris prieš perjungimą patikrina SHA256, atvaizdą, migracijas
  švarioje laikinoje DB ir sukuria produkcinės DB kopiją.

## [0.11.1 BETA] - 2026-07-29

### Pridėta

- Vaikas, savo įrenginyje įjungęs pranešimus, gauna tik jam skirtą push
  pranešimą, kai tėvai patvirtina arba atmeta jo darbą, grąžina darbą pataisyti
  arba patvirtina ar atmeta prizo prašymą. Pranešime pateikiamas ir tėvų
  komentaras ar atmetimo priežastis, jei jie buvo įrašyti.

### Pataisyta

- Darbo pateikimo ir prizo prašymo sėkmės efektai veikia ir „iPhone“ bei
  „iPad“: garsas atrakinamas vaiko paspaudimu, tačiau kartu su konfeti
  paleidžiamas tik serveriui sėkmingai priėmus veiksmą. Klaidos ar puslapio
  atnaujinimas efekto nepaleidžia pakartotinai.
- Mobiliajame laukiančių prašymų rodinyje darbo informacija ir trys sprendimo
  piktogramos išdėstytos kompaktiškai, su vienodomis paspaudimo zonomis ir
  aiškia žalios, violetinės bei raudonos spalvų reikšme.
- Garso mygtukas naršyklėje ir iOS vienodai rodo būseną: žalia reiškia įjungtą,
  o raudona – išjungtą garsą.
- Darbo grąžinimo pataisyti ir atmetimo dialoguose, pasirinkus lietuvių kalbą,
  nebelieka angliškų paaiškinimų bei laukų pavadinimų.

## [0.11.0 BETA] - 2026-07-29

### Pridėta

- Prisijungę tėvai ir vaikai gali prieinamu plaukiojančiu vabalo mygtuku
  pateikti problemą arba pasiūlymą. Vaikams naudojami paprastesni klausimai.
- Atsiliepimas pirmiausia išsaugomas KinKudos, o tik tada pasirinktinai
  siunčiamas el. pašto pranešimas. Diagnostikoje nerenkami slaptažodžiai, PIN
  kodai, slapukai, sesijos raktai ar kitų formų turinys.
- Pasirinktinės ekrano nuotraukos patikrinamos, išvalomos nuo metaduomenų,
  sumažinamos, konvertuojamos į privatų WebP failą ir pasiekiamos tik jų
  autoriui arba tėvams.
- Tėvai „Nustatymuose“ gali filtruoti atsiliepimus, peržiūrėti diagnostinį
  kontekstą, atidaryti privačią nuotrauką ir keisti būseną į „Naujas“,
  „Peržiūrėtas“, „Planuojamas“ arba „Išspręstas“.
- Bendrinis `KINKUDOS_FEEDBACK_EMAIL` nustato pranešimų gavėją, o išspręstų
  atsiliepimų nuotraukų saugojimo trukmę galima pasirinkti nustatymuose.
  Nuotraukas valo esamas naktinis priežiūros darbas.
- Diegimui pridėta bendrinė `configure-feedback.sh` komanda, kuri saugiai
  nustato atsiliepimų pranešimų gavėją esamame `.env`, nekeičiant SMTP
  tiekėjo konfigūracijos.

### Pataisyta

- Darbų su nuotrauka patvirtinimo kortelės tapo kompaktiškos ir nebeiškreipia
  išdėstymo telefone ar kompiuteryje. Nuotrauka rodoma apkarpytoje miniatiūroje
  ir atidaroma pilno dydžio peržiūroje.
- Darbo patvirtinimo, grąžinimo pataisyti ir atmetimo veiksmai pateikiami
  vienodo dydžio aiškiomis SVG piktogramomis. Grąžinant arba atmetant atidaromas
  dialogas su neprivalomu komentaru, kurį, jei įrašytas, mato vaikas.
- Atmesti darbai nebepradingsta: tėvų veiksmų istorijoje jie rodomi pagal
  sprendimo laiką su raudona „stop“ būsena, neprivalomu komentaru ir, kol
  saugoma, darbo nuotraukos peržiūra. Atmetimas nekeičia vaiko balanso.
- Sutvarkytas tėvų erdvės nuotraukų peržiūros dialogo susiejimas, todėl
  paspaudus kameros ikoną istorijoje arba darbo miniatiūrą nuotrauka vėl
  atidaroma pilno dydžio peržiūroje.
- Tėvų veiksmų istorijoje dabar rodomi atmesti prizų prašymai su raudona
  „stop“ būsena ir atmetimo priežastimi. Patvirtinti prizų prašymai pažymimi
  žalia patvirtinimo būsena; abiem atvejais veikia vaikų filtras ir
  puslapiavimas.
- Viešas pakeitimų puslapis atpažįsta lietuviškas Markdown skilčių antraštes,
  todėl 0.10.3, 0.10.4 ir vėlesnių versijų pataisymai nebebus rodomi kaip
  tušti.
- Vaiko garso valdiklis naudoja storesnę SVG garso ikoną ir tokią pačią
  44 px aukščio kapsulės formą kaip gretimi viršutinės juostos valdikliai.
## [0.10.4 BETA] - 2026-07-29

### Pataisyta

- „Safari“ perjungiant tėvų erdvės skyrius puslapis lieka viršuje, todėl
  pasirinkto skyriaus turinys nebepasislepia po lipnia viršutine juosta. CSS,
  „JavaScript“ ir programos podėlis versijuojami, kad naršyklės tikrai pasiimtų
  pataisą.
- „Pradžios“, „Darbų ir prizų“ bei „Nustatymų“ antraštės prasideda vienodame
  aukštyje, o kairiojo meniu ikonos ir tekstai lygiuojami pagal bendras ašis.

## [0.10.3 BETA] - 2026-07-29

### Pataisyta

- Tėvų nustatymų puslapyje naudojama trumpa antraštė „Nustatymai“.
- Visuose viešuose puslapiuose naudojama vienoda lengva „KinKudos“ produkto
  antraštė, o prisijungusių tėvų ir vaikų erdvėse išlieka šeimos kontekstas.
- Telefone, planšetėje ir kompiuteryje suvienodinti tarpai tarp laukiančių
  prašymų ir vaikų kortelių.
- Kalbos pasirinkimas ir pranešimų valdiklis yra tiksliai vienodo aukščio, o
  keturi mobilios navigacijos punktai turi vienodus stulpelius ir centrus.
- Aktyvūs ir neaktyvūs prizų mygtukai visose vaikų temose išlaiko vienodus
  matmenis.

## [0.10.2 BETA] - 2026-07-29

### Fixed

- Prizo prašymo veiksmas aktyvus tik tada, kai konkretaus prizo kainą padengia
  vaiko dabartinis balansas ir jam nustatytas kreditas. Serveris per brangų
  prašymą atmeta ir bandant apeiti sąsają.
- „iPhone“ sumažintas tarpas tarp laukiančių prašymų ir vaikų kortelių, o visi
  keturi apatinės navigacijos punktai išdėstyti vienodo pločio stulpeliuose ir
  tiksliai išcentruoti.
- Kompaktiškas kalbos pasirinkimas savo aukščiu ir kapsulės forma suvienodintas
  su pranešimų valdikliu, išlaikant centruotą tekstą ir 44 px paspaudimo zoną.
- Kredito limito informacijos ikona vertikaliai išcentruota su užrašu.
- Viešame landing puslapyje šeimos valdymo juostą pakeitė lengva produkto
  antraštė; šeimos vardas paliktas pagrindiniame pasveikinime, o versijos
  nuoroda perkelta į puslapio apačią.
- Programos ikona atnaujinta į aiškią gintaro ir šalavijo spalvų „KK“
  monogramą šiltame „KinKudos“ violetiniame fone. Atnaujinti PWA, „iOS“ ir
  pranešimų dydžiai bei pridėtas ikonų talpyklos versijavimas.

## [0.10.1 BETA] - 2026-07-29

### Fixed

- Lietuviškuose puslapiuose nebesimaišo angliškos antraštės, pagalbiniai
  tekstai, mygtukai ir pradinio puslapio tekstas.
- Supaprastinta tėvų erdvės antraščių hierarchija: pašalintos perteklinės
  mažosios antraštės, suvienodinti nustatymų skyrių tarpai.
- „Safari“ ir „iOS“ kalbos vėliava bei kodas geometriškai išcentruoti,
  išlaikant atskirą rodyklę ir 44 px paspaudimo zoną.
- Tėvų ir pradžios sąsajų spalvos patikrintos pagal oficialią „KinKudos“
  paletę, įskaitant tamsią temą ir semantines būsenų spalvas.

## [0.10.0 BETA] - 2026-07-29

### Added

- Vaikas prie atlikto darbo gali pasirinktinai pridėti nuotrauką iš kameros ar
  galerijos. HEIC ir HEIF saugiai konvertuojami į privačius WebP failus.
- Tėvai darbą gali patvirtinti, atmesti arba grąžinti pataisyti; vaikas gali
  pakeisti nuotrauką ir pateikti darbą iš naujo.
- Pridėtas nustatomas taškų priedas už nuotrauką ir automatinis senų nuotraukų
  išvalymas.
- Vaikų pranešimai, sėkmės konfeti, teminiai garsai ir garso išjungimas.
- Mobilioji tėvų erdvė su skyriais „Pradžia“, „Darbai ir prizai“,
  „Nustatymai“ ir „Istorija“.
- Išnaudojus pusę kredito, naujų prizų prašymai pristabdomi iki balanso
  pagerėjimo.

### Changed

- Bendrinė valiuta pakeista į taškus. Blokų pasaulyje naudojami smaragdai, o
  Magijos akademijoje – galeonai, su taisyklingais skaičių linksniais.
- Vaikų temų navigacija ir veiksmai naudoja sutartus kiekvieno pasaulio
  pavadinimus.
- Tėvų ir pradinė erdvės naudoja oficialią šiltos slyvų, šalavijo, gintaro,
  kreminę ir anglies spalvų paletę.
- Blokų pasaulis gavo kampuotas pikselines korteles, o Magijos akademija –
  auksinius rėmelius ir vaško antspaudo pojūčio mygtukus.

### Fixed

- Ilgi darbų pavadinimai ir tuščios istorijos tekstas nebeišlipa iš rėmų.
- iPad ekrane darbų kortelėse išlaikytas skaitomas teksto plotis ir pilno
  pločio veiksmo mygtukai.
- Vėliava ir kalbos kodas pasirinkime sulygiuoti per centrą.
- Naujo pasiūlymo ikonos laukas pradedamas tuščias.

## [0.9.1 BETA] - 2026-07-29

### Fixed

- Neigiamos tokenų reikšmės visur rodomos raudonai. Prizų kainoms nebenaudojama
  teigiamų reikšmių žalia spalva.

## [0.9.0 BETA] - 2026-07-29

### Added

- Suskleidžiama tėvų veiksmų istorija su 10 įrašų puslapyje, lokalizuotu
  puslapiavimu ir filtru pagal vaiką.
- Nuolatiniame lietuvių ir anglų kalbų pasirinkime pridėtos šalių vėliavos.
- Balansuose, kataloguose, prašymuose ir veiksmų istorijoje naudojami taisyklingi
  lietuviški bei angliški tokenų linksniai.

### Changed

- Darbų, nuobaudų ir prizų sumos laukas vienodai vadinamas „Tokenai“.
  Nuobaudai įvedamas teigiamas skaičius, kurį sistema pritaiko kaip nuskaitomą
  sumą.
- Katalogų ir skyrimo dialogų tokenų tipografika suvienodinta: darbai ir prizai
  rodomi žaliai, nuobaudos – raudonai.
- Visų naršyklės skirtukų pavadinimai atitinka formatą „Puslapis – KinKudos“,
  o pagrindiniame puslapyje įtraukiamas šeimos slapyvardis.
- Viršutinėje juostoje „šeima“ ir „family“ rašoma mažąja raide.

### Fixed

- Nulinės ir neigiamos katalogų sumos atmetamos su lokalizuotu paaiškinimu.

## [0.8.5 BETA] - 2026-07-28

### Added

- Visa vartotojo sąsaja veikia anglų ir lietuvių kalbomis, o pasirinkta kalba
  išsaugoma įrenginyje.
- Naršyklės kalbos atpažinimas; naujose instaliacijose numatytoji kalba yra
  anglų.
- Dvikalbė pirmojo paleidimo instaliacija ir bendrinis šeimos sukūrimas.
- Atskiros angliškos ir lietuviškos pakeitimų istorijos.
- Pirmą kartą prisijungęs vaikas privalo pasirinkti savo aplinką; iki tol
  rodoma neutrali sąsaja.
- Kuriant šeimą privaloma nurodyti jos pavadinimą arba slapyvardį, kuris
  sąsajoje jungiamas su lokalizuotu žodžiu „Šeima“ arba „Family“.

### Changed

- Produktas nuo šiol vadinamas „KinKudos“. Šeimos pavadinimas lieka atskiru,
  konkrečios instaliacijos duomeniu ir privalomai įvedamas pirmojo paleidimo
  metu.
- Naujose angliškose instaliacijose numatytasis valiutos pavadinimas yra
  `Tokens`.
- Ankstesnis konkrečios šeimos vardas pašalintas iš programos kodo, failų,
  konfigūracijos kintamųjų, Docker resursų, slapukų, atsarginių kopijų ir
  dokumentacijos. Vidiniai vardai dabar yra neutralūs.
- Viešos GitHub dokumentacijos pagrindinė kalba pakeista į anglų.
- Lietuviškas vardo kreipinys naudojamas tik pasirinkus lietuvių sąsają.
- Atnaujinus esami vaikų profiliai lieka paruošti naudoti ir neprivalo iš naujo
  atlikti pirmojo prisijungimo pasirinkimo.

## [0.8.0 BETA] - 2026-07-28

### Added

- Tėvai vienu veiksmu gali pažymėti ir vaikui priskirti kelis atliktus darbus
  arba kelias nuobaudas.
- Pasirinkimai dialoguose rodomi kaip aiškus checkbox sąrašas su kiekvieno
  įrašo ikona ir tokenų verte.

### Changed

- Keli vienu veiksmu pažymėti įrašai išsaugomi atskiromis veiksmų istorijos
  eilutėmis ir apdorojami viena duomenų bazės transakcija.

## [0.7.0 BETA] - 2026-07-28

### Added

- Saugus tėvų slaptažodžio atkūrimas vieną valandą galiojančia el. pašto nuoroda.
- El. pašto adresas kuriant ir redaguojant tėvų paskyras.
- Nuo konkretaus tiekėjo nepriklausoma SMTP konfigūracija per aplinkos
  parametrus ir atskirą Docker secret failą.
- Viešas, versijomis suskirstytas pakeitimų istorijos puslapis su skyriais
  „Kas naujo?“ ir „Kas pataisyta?“.
- Sąsajoje rodomas versijos numeris dabar atveria pakeitimų istoriją.

### Security

- Atkūrimo forma neatskleidžia, ar nurodytas el. pašto adresas egzistuoja.
- SMTP slaptažodis nepatenka į Docker atvaizdą ar Compose aplinkos failą.

## [0.6.0 BETA] - 2026-07-28

### Added

- Raudonas „Trinti“ mygtukas darbų, nuobaudų ir prizų redagavimo formose.
- Patvirtinimas prieš katalogo įrašo trynimą.

### Changed

- Katalogo įrašai trinami saugiai: išnyksta iš sąrašų, tačiau ankstesni
  prašymai, balansai ir veiksmų istorija išlieka.
- Naujų darbų, nuobaudų ir prizų ikonos laukas pagal nutylėjimą yra tuščias.

## [0.5.0 BETA] - 2026-07-28

### Added

- Aiškus pranešimų valdiklis su SVG varpelio piktograma, tekstine būsena ir
  iPhone naudojimo paaiškinimu.
- Visose vartotojui matomose versijos žymose rodoma `BETA`.

### Changed

- Balanso skaičius išlaiko teigiamos arba neigiamos reikšmės spalvą, o
  `TOKENAI` rodomas pagrindine teksto spalva.
- „Kreditas iki“ pakeistas į „Kredito limitas“.
- Visi katalogai atidarius puslapį yra suskleisti.
- Magijos akademijos mygtukas pataisytas į „Siųsti pelėdą“.

## [0.4.0] - 2026-07-28

### Added

- Tėvų ir vaikų paskyrų redagavimas bei saugus išjungimas neprarandant istorijos.
- Keturi greiti veiksmai kiekvieno vaiko kortelėje: atliktas darbas, nuobauda, kreditas ir kitas įvertinimas.
- iPhone HEIC/HEIF avatarų priėmimas ir konvertavimas į WebP.
- Laukiančių prašymų skaičius skyriaus antraštėje.
- Rankinis ir automatinis trumpųjų pranešimų uždarymas.

### Changed

- Kataloguose esami įrašai aiškiai atskirti nuo „Pridėti naują“ formų.
- Paskyrų kūrimas ir redagavimas padalyti į atskirus vienodo stiliaus blokus.
- Vaiko kortelių balanso, valiutos ir kredito tipografika suvienodinta.
- Nuobaudos skyrimas perkeltas iš katalogo į konkretaus vaiko kortelę.
- Slaptažodžių paaiškinimai pateikiami lietuviškai.

## [0.3.0] - 2026-07-28

### Added

- Lietuviški vaikų vardų kreipiniai su galimybe juos patikslinti kuriant profilį.
- Naujų tėvų prisijungimų ir vaikų profilių kūrimas tėvų erdvėje.
- Aiški šio įrenginio Web Push būsena ir pranešimų išjungimas.
- „Nuobodų“ skyrimas pasirinktam vaikui tiesiai iš katalogo.
- Kompaktiškas vaiko kredito keitimo dialogas.

### Changed

- Laukiantys prašymai grupuojami pagal vaiką ir rodomi nuo seniausio.
- Tėvų antraštė sutrumpinta, o vaikų kortelėse avataras rodomas šalia vardo.
- „Bausmės“ vartotojo sąsajoje pervadintos į „Nuobodas“.
- Valdymo emoji pakeisti lokaliais SVG simboliais.

## [0.2.0] - 2026-07-28

### Added

- Vaiko avataro įkėlimas, kvadratinis apkirpimas ir rodymas profiliuose.
- Vaiko PIN keitimas, patvirtinant dabartinį PIN.
- Unicode emoji pasirinkimas darbams, bausmėms, prizams ir pasiūlymams.
- Darbų, bausmių ir prizų redagavimas tėvų erdvėje.
- Programos versijos rodymas sąsajoje ir diagnostiniame `/health/` atsakyme.

### Changed

- Teigiami balansai tėvų erdvėje rodomi žaliai, neigiami – raudonai.
- Atnaujinti pagrindinio puslapio tekstai.
- Katalogų slėpimo ir redagavimo veiksmai pakeisti į kompaktiškas ikonas.
- Senos tekstinės ikonų reikšmės migracijos metu konvertuojamos į emoji.

### Fixed

- Web Push klaida nebesukelia HTTP 500 pateikiant vaiko atliktą darbą.
- Gunicorn nebebando kurti valdymo lizdo tik skaitymui skirtoje failų sistemoje.
- Diegimas nutraukiamas, jei nepavyksta duomenų bazės migracija.

## [0.1.0] - 2026-07-28

### Added

- Tėvų ir vaikų prisijungimai su saugiomis sesijomis bei PIN užraktu.
- Darbų, bausmių, prizų, pasiūlymų ir taupymo tikslų darbo eiga.
- Nekintama tokenų operacijų istorija ir keičiamas minusinis limitas.
- Originalios „Magijos akademijos“ ir „Blokų pasaulio“ temos.
- PWA diegimas, neprisijungus rodomas ekranas ir Web Push.
- ARM64 / AMD64 Docker bei Traefik konfigūracija.
- SQLite ir šifruotų Backblaze B2 kopijų įrankiai.
- Pirmojo paleidimo, atkūrimo kodo ir VAPID raktų komandos.
