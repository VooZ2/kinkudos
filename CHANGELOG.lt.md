# Changelog

Visi reikšmingi projekto pakeitimai dokumentuojami šiame faile.

Formatas paremtas „Keep a Changelog“, o versijoms naudojama `YY.FEATURE.FIX`
schema.

## [Unreleased]

## [26.6.0] - 2026-08-06

### Pridėta

- Taupymo tikslai dabar turi du būdus: gyvą **Dabartinio tikslo** pažangą iš
  turimų taškų arba konkrečiam tikslui atskirai išsaugotus taškus.
- Patvirtinto taupymo tikslo kortelėje vaikas dabar gali pasirinkti taupymo
  būdą.
- Atskirai išsaugoti taškai palaiko atominius pervedimus ir grąžinimus, tėvų
  tvirtinamą užbaigimą, tikslų istoriją bei vaiko ir tėvų valdymo sąsają.
- Istorija dabar apima taupymo būdo pasirinkimą, taškų perkėlimus ir
  grąžinimus, Dabartinio tikslo pakeitimus, tikslo užbaigimą ir ištrynimą.
- Tėvų darbo erdvėje pasiekiamas atskiras tikslų valdymas ir Istorijos filtrai.

### Pakeista

- Veiksmų istorijoje neberodomas įvykių skaičiaus ženklelis, o tuščių būsenų
  tekstas naudoja tokią pačią antrinę tipografiją kaip kredito suvestinės.
- Informaciniai dialogai uždaromi vienodu uždarymo valdikliu be pasikartojančių
  **Supratau** mygtukų, o jų aprašų tipografija suvienodinta.
- Tėvų erdvėje dabar yra Pradžios, Tvarkyti, Nustatymų ir Istorijos navigacija,
  o „Tvarkyti“ turi atskiras Darbų, Nuobaudų, Prizų ir Tikslų skiltis.
- Tėvų Pradžioje yra kompaktiška laukiančių prašymų tuščia būsena, aiškesnės
  vaikų kortelės, išleidžiamų ir išsaugotų taškų suvestinės, tikslų suvestinės
  bei pavadinti greitieji veiksmai.
- Nustatymai suskirstyti į prisitaikančias Šeimos, Taškų ir darbų, Nutrinamų
  bilietų, Duomenų ir saugojimo, prieigos, paslaugų, paskyrų ir atsiliepimų
  grupes.
- Vaiko tikslų kortelėse, kai pakanka vietos, darbalaukyje naudojamas dviejų
  stulpelių išdėstymas, išlaikant teminę vaiko išvaizdą.
- Tėvų ir vaikų valdikliai naudoja vientisas vietines SVG ikonas ir prieinamus
  veiksmų pavadinimus, išlaikant tikslo emoji personalizavimą.

### Pataisyta

- Valdymo skilčių nuorodos dabar palieka atidarytą tėvų skydelį ir išskleidžia
  pasirinktą Darbų, Nuobaudų, Prizų arba Tikslų skiltį.
- Išsaugoto tikslo **Po** peržiūra ir jos etiketė bei vienetas lieka vienoje
  eilutėje, o suma atsinaujina renkantis vertę.
- Taupymo būdo dialogo veiksmai nebesidengia, o katalogo rodymo/slėpimo
  valdikliai išlaiko suderintas ikonas ir prieinamus pavadinimus.
- Tikslų valdymo eilutėse progreso ir taupymo būdo stulpeliai išlieka vienoje
  vietoje, o tikslo kortelės nebesiliečia ir nepersidengia.
- Taupymo tikslų pasiūlymų tarpai ir suma sutampa su darbų bei prizų prašymais,
  o siūloma suma išlieka neutralios spalvos.
- Tėvų katalogų redagavimas naudoja oficialią reguliarią `pen-to-square` ikoną,
  o išskleistame tikslo redaktoriuje rodomas tik tekstinis **Trinti** veiksmas
  su aiškiu patvirtinimu.
- Istorijos vaiko pasirinkimas dabar pritaikomas iškart ir išsaugo kitus
  aktyvius URL filtrus.
- **Pridėti taškų** peržiūroje pasirinkimas **Visi** apribojamas turimais
  taškais ir iki tikslo likusia suma.
- Veiksmų istorijos eilutėse neberodomos klaidinančios kalendoriaus ikonos,
  o **Informational** ženklelis neutralus ir veiklos ikona rodoma rezultato
  srityje.
- Ištrinant tikslą jo išsaugoti taškai atominėje transakcijoje grąžinami,
  laukiantys užbaigimo prašymai atšaukiami, o įvykių istorija išsaugoma.
- Tėvų skydelio greitųjų veiksmų ikonos bei kompaktiškos kredito ir bilietų
  eilutės yra vienodo dydžio, o kopijų įspėjimai atskirti.
- Tik vėliavas rodantis kalbos meniu dabar lieka tiksliai centruotas po savo
  mygtuku siauruose ir plačiuose ekranuose bei neuždengia kitų antraštės veiksmų.
- Tėvų istorija dabar apriboja kiekvieną veiklos šaltinį prieš sujungdama 50
  naujausių įrašų, todėl „Bet kada“ nebekrauna neribotos istorijos į atmintį.

Po migracijos esamas vaikas, turintis vieną aktyvų tikslą, išlaiko turimus
taškus naudojančią pažangą. Vaikai, turintys kelis aktyvius tikslus, taupymo
būdą pasirenka patys, o tikslas nenustatomas spėjant.

### Saugumas

- Kai įrenginių susiejimas įjungtas, vaikų avatarus dabar gali gauti tik
  prisijungęs tėvas arba galiojantį susietą įrenginį turintis klientas, todėl
  anonimiškai perrinkti profilių paveikslėlių pagal ID nebegalima.
- Lygiagretūs tikslo užbaigimo prašymai dabar grąžina valdomą validacijos
  klaidą, o pataisyta `cryptography` priklausomybė užfiksuota ties 50.0.0.

## [26.5.3] - 2026-08-06

### Pakeista

- Prisijungusių tėvų ir vaikų puslapiai dabar naudoja vientisą, nuo lango
  kraštų atitrauktą produkto antraštę kaip pasveikinimo puslapyje, o ne atskirą
  viso pločio meniu juostą.
- Pradinis paruošimas dabar neutraliai paaiškina paruošimo kodą, kviečia
  paruošti sistemą, o pasirenkamo el. pašto žymimąjį langelį rodo iškart už jo
  teksto toje pačioje eilutėje. Kompiuteryje forma taip pat naudoja patogų dviejų
  stulpelių išdėstymą, vienodo dydžio laukus ir aiškius teksto tarpus, o
  telefone lieka vieno stulpelio. SMTP laukai rodomi neaktyvūs, kol
  nepasirenkamas el. pašto nustatymas.
- Pirmojo vaiko prisijungimo ekrane kiekvienas pasaulis dabar rodomas kaip
  pilna temos peržiūra su aiškia ir prieinama pasirinkimo būsena kompiuteryje
  bei telefone.

### Pataisyta

- Vaiko PIN dialogo pateikimo mygtukas dabar vadinamas „Prisijungti“ vietoje
  nesusijusios būsenos teksto.
- Prisijungimo ir kiti sesijai jautrūs puslapiai dabar neleidžia naršyklei ar
  PWA pateikti pasenusios kopijos, saugiai atsinaujina po Back/Forward Cache
  atkūrimo ir apsaugo tėvų prisijungimo formą nuo dvigubo pateikimo.
- Service worker dabar apeina autentifikacijos maršrutus, visada
  persitikrinamas ir toliau podėlyje laiko tik versijuotą offline puslapį.

## [26.5.2] - 2026-08-04

### Pridėta

- „Hostinger Docker Manager Catalog“ Compose profilis paleidžia „KinKudos“
  aplikaciją už esamo „Hostinger Traefik“ serviso, o visus būtinus vykdymo
  duomenis laiko viename išliekančiame vardiniame tome.
- Pirmą kartą paleistas aplikacijos konteineris išliekančiame tome sukuria ir
  išsaugo „Django“ paslaptį bei VAPID raktus.

### Pakeista

- „Hostinger Catalog“ MVP sąmoningai neįtraukia „KinKudos“ kopijų agento,
  nekonfigūruoja ir nenaudoja „Restic“, nereikalauja kopijų prisijungimo
  duomenų ar prieigos prie „Docker“ lizdo. Išbandytas MVP atkūrimo kelias
  naudoja viso „Hostinger VPS“ momentines kopijas, tačiau jos nėra perkeliamas
  aplikacijos lygio „KinKudos“ backup.

### Saugumas

- Automatiškai sugeneruotos „Hostinger“ vykdymo paslaptys sukuriamos tik
  savininkui pasiekiamomis teisėmis ir nėra generuojamos iš naujo perkraunant
  konteinerį, perkuriant Compose, vykdant „Docker Manager“ atnaujinimą,
  perkraunant VPS ar atkuriant momentinę kopiją.

## [26.5.1] - 2026-08-03

### Pridėta

- Pasirenkamas Hostinger VPS diegiklis dabar patikrina pasirinktą leidimą ir
  paruošia idempotentinę Ubuntu 24.04 Docker instaliaciją su prisegtos versijos
  „Caddy“ HTTPS proxy, išliekančia sertifikatų saugykla, aiškiomis diegimo
  būsenomis bei saugiu tęsimo ir sustabdymo procesu.
- Programos poraštė pagal aktyvią sąsajos kalbą pateikia nuorodą į anglišką
  arba lietuvišką „KinKudos“ dokumentaciją.

### Pakeista

- Hostinger instaliacijos pernaudoja standartinį atsarginių kopijų agentą ir
  turi stabilų versijuotą diegimo profilio žymenį, todėl atnaujinimai, būklės
  patikros bei saugus sustabdymas režimo nenustato pagal proxy failus.

### Saugumas

- Hostinger diegiklis prieš paleisdamas leidime esantį bootstrap patikrina
  SHA256 kontrolinę sumą, neviešina Gunicorn ir tęsdamas atpažintą instaliaciją
  išsaugo esamas paslaptis bei setup kodą.

## [26.5.0] - 2026-08-03

### Pridėta

- Naujos instaliacijos pirmą paruošimą dabar užbaigia naršyklėje: vedlys
  sukuria pirmą tėvų administratorių, šeimos pavadinimą, numatytąją kalbą,
  laiko juostą, atkūrimo kodą ir pasirinktinius SMTP nustatymus.
- Vokiškoje ir prancūziškoje dokumentacijoje dabar pateikiami lokalizuoti
  tituliniai, tinkamumo, savarankiško diegimo, pirmojo paruošimo ir vaiko
  įrenginio susiejimo vadovai.
- Vieša angliška naudotojo dokumentacija dabar apima pradžią, tėvų veiksmus, nustatymus, saugumą, priežiūrą ir greitą pagalbą; iš kiekvienos skilties pasiekiami lietuviški atitikmenys.
- Viešos saugumo pranešimo ir leidimų bei palaikymo politikos paaiškina privatų
  pažeidžiamumų kanalą, palaikomos versijos ribas ir pagal galimybes teikiamo
  palaikymo apimtį.
- Viešas vadovas dabar pateikia anglišką ir lietuvišką pradžios kelią,
  konkrečius tėvų darbo srautus bei serverio diegimo ir atkūrimo apžvalgas.
- Šeimos administravimą, duomenų ribas, palaikymo ribas ir privatų saugumo
  pranešimą dabar lengviau rasti viešame vadove.

### Pakeista

- Diegiklis dabar paruošia ir paleidžia KinKudos, parodo privatų naršyklės
  setup kodą ir terminale nebeprašo šeimos prisijungimo duomenų, vardų ar
  vaikų PIN.
- Šeimos laiko juosta dabar nustato su kalendoriumi susijusį užklausų bei
  loterijos priminimų veikimą, o pasirinkta numatytoji kalba naudojama
  naršyklėse be išsaugoto pasirinkimo.
- Katalogo kūrimo, redagavimo, rodymo/slėpimo ir šalinimo veiksmai grįžta į
  darbų ir prizų skiltį, o ne tėvų pradžios skiltį.
- Plaukiojanti šeimos atsiliepimų forma rodoma tik vaikams; tėvai vaikų
  atsiliepimus ir toliau peržiūri nustatymuose.
- Dokumentacijos kalbos pasirinkimas, metaduomenys, struktūriniai duomenys ir
  greito starto navigacija dabar palaiko EN, LT, DE ir FR, nerodydami neišverstų
  skilčių kaip lokalizuoto turinio.
- Vieša dokumentacija dabar naudoja KinKudos ikoną, spalvų paletę, tipografiją ir šviesios bei tamsios išvaizdos stilių.
- Vieša dokumentacija dabar pateikia lokalizuotus pavadinimus, aprašymus,
  kalbos metaduomenis, kanonines ir alternatyvių kalbų nuorodas, dalinimosi
  peržiūras bei paieškos robotų nurodymus anglų ir lietuvių puslapiams.
- Viešoje dokumentacijoje darbų ir prizų apžvalgos dabar matomos tėvų
  navigacijoje, publikuojami svetainės bei naršymo kelio struktūriniai duomenys
  ir pateikiama su „Traefik“ suderinama santykinių Nginx peradresavimų konfigūracija.
- Lietuviškos dokumentacijos visas šoninis meniu ir jo nuorodos dabar įrašomi
  tiesiai sugeneruotame HTML, nepaliekant vertimo naršyklės JavaScript kodui.
- Lietuviškuose puslapiuose dabar parenkama ir išskleidžiama ta pati aktyvi
  šoninio meniu skiltis kaip angliškuose atitikmenyse.

### Pataisyta

- Laukiančių darbų ir prizų kortelėse iPhone dydžio ekranuose antraštės bei
  taškų tarpai dabar kompaktiški ir vienodi.

### Saugumas

- Serverio sugeneruotas setup kodas ir serverio pusėje saugoma užbaigimo būsena
  neleidžia naujoje viešoje instaliacijoje sukurti daugiau nei vieno pradinio
  administratoriaus.

## [26.4.9] - 2026-07-31

### Pataisyta

- Vieši, prisijungimo, įrenginio susiejimo ir pirmojo paruošimo ekranai dabar
  naudoja bendrą spalvingą sistemos apvalkalą ir iki tėvų ar vaiko vidinės
  sąsajos įjungimo prisitaiko prie įrenginio šviesios arba tamsios išvaizdos.

## [26.4.8] - 2026-07-31

### Pridėta

- Nedidelis viešas diegiklis gali atsisiųsti ir patikrinti naujausią leidimą,
  o tada paleisti esamą vedamą „Docker Compose“ paruošimą.

### Pakeista

- Skelbiamos instaliacijos dabar versijuotą kelių platformų programos atvaizdą
  parsisiunčia iš viešos `vooz2/kinkudos` „Docker Hub“ saugyklos.

## [26.4.7] - 2026-07-31

### Pakeista

- Pagrindinis, tėvų prisijungimo ir slaptažodžio atkūrimo ekranai dabar turi
  bendrą šviesesnį, CSS gradientais sukurtą dizainą be papildomų paveikslėlių.
- GitHub README dabar pateikia vaizdinę produkto apžvalgą, kviečia pirmiausia
  išbandyti demonstraciją, glaustai paaiškina diegimą ir nurodo pasirenkamą VPS alternatyvą.
- Vaiko loterijos kortelėje ir pirkimo dialoge dabar rodoma aiškesnė „Loterijos bilietų“ etiketė.

### Saugumas

- Atsarginių kopijų tiekėjas dabar nustatomas iš sukonfigūruotos S3 saugyklos URL hosto, o ne pagal bet kur rastą URL teksto dalį.

## [26.4.6] - 2026-07-31

### Pakeista

- README dabar pateikiama viešos demonstracijos nuoroda ir tėvų bei vaikų
  prisijungimo duomenys.

### Pataisyta

- Lietuviškame atsiliepimų nustatymų tekste nebeliko bereikalingos priešpriešos
  tarp atsiliepimų išsaugojimo ir nesukonfigūruotų el. pašto pranešimų.

## [26.4.5] - 2026-07-31

### Pataisyta

- Tėvai dabar gauna „Web Push“ pranešimą, kai vaikas paprašo prizo.
- „Web Push“ pranešimai dabar apima ir vaiko pasiūlymus bei gimimo datos
  pakeitimo prašymus, o vaikui išsiunčiami tėvų sprendimai.

## [26.4.4] - 2026-07-31

### Pakeista

- Diegimo dokumentacijoje dabar aprašytas tuščio „Ubuntu“ serverio paruošimas:
  „Docker Engine“, Docker Compose, „GitHub CLI“ ir „Caddy“ HTTPS proxy diegimas
  prieš paleidžiant KinKudos vedlį.

### Pataisyta

- Išjungti IP ribojimai dabar žymimi raudona neaktyvios būsenos spalva, o
  įjungti ribojimai lieka žali.
- Atsiliepimų administravimo blokas lygiuojamas kaip kiti nustatymų blokai ir
  palieka vienodą tarpą po paaiškinimu.
- Atsiliepimo ekrano nuotraukos pasirinkimo valdiklis paveldi bendrą sąsajos
  tipografiką vietoje nederančio naršyklės mygtuko šrifto.

## [26.4.3] - 2026-07-31

### Pataisyta

- Vaiko įrenginio susiejimo nuorodą dabar galima patvirtinti „Safari“
  naršyklėje negaunant CSRF 403 atsako. Susiejimo puslapis išsaugo „Django“
  reikalingą tos pačios svetainės nuorodos šaltinį, o vienkartinis kodas lieka
  URL fragmento dalyje.

## [26.4.2] - 2026-07-31

### Pakeista

- Tinklo prieigos nustatymuose aiškiai rodoma aktyvi būsena, paaiškinama,
  kurioms sritims taikomi IP ribojimai, pateikiamas leidžiamų tinklų sąrašas,
  o redagavimas perkeltas į su kitais paslaugų nustatymais suderintą dialogą.
- Katalogų pavadinimams aiškiai pritaikyta bendra sistemos tipografija.

### Pataisyta

- Atsiliepimų administravimo bloke neberodomas čia neaktualus viešo skelbimo
  „GitHub“ privatumo įspėjimas.
- Poraštėse pridėta kompaktiška programos klaidos pranešimo nuoroda.

## [26.4.1] - 2026-07-31

### Pakeista

- Tėvų ir vaikų prašymų srautuose patvirtinimo, atlikimo, taisymo, atmetimo,
  atšaukimo, prizo prašymo bei prizo ar tikslo siūlymo veiksmai rodomi
  nuosekliomis ikonomis be teksto.
- Sutrumpinti ir patikslinti lietuviški nustatymų bei atsiliepimų tekstai.
- Diegimo reikalavimuose nebeliko konkretaus prižiūrėtojo registro prisijungimo
  komandos ir su vienu leidimu susieto migracijos pranešimo.

### Pataisyta

- Veiksmų ikonų spalvos atitinka jų būseną, o tėvų ir vaikų ekranuose ikonos
  išlieka vienoje eilėje.
- Vaikų įrenginio susiejimo veiksmai telpa vienoje adaptyvioje dviejų stulpelių
  eilėje ir nebesidengia.
- Tėvų atsiliepimų skiltyje rodomas kompaktiškas privatumo įspėjimas, o vietoje
  didelio pasikartojančio klaidos pranešimo mygtuko naudojama esama GitHub
  nuoroda poraštėje.

## [26.4.0] - 2026-07-31

### Pridėta

- Tėvai trumpalaike vienkartine nuoroda gali susieti kiekvieną vaiko naršyklę
  arba įdiegtą PWA, peržiūrėti susietus įrenginius, juos pervadinti ir atšaukti
  vieno arba visų įrenginių prieigą. Vaiko PIN lieka antras patvirtinimo
  žingsnis.
- Tėvai pasirinktinai gali apriboti vaikų puslapius arba visą programą
  konkrečiais IP adresais ir CIDR tinklais. Netyčia užsirakinus apribojimą
  galima išjungti serverio komanda.
- Produkcinis diegimas palaiko serveryje veikiantį „Nginx“ ar „Caddy“,
  konteinerinius proxy, tokius kaip „Nginx Proxy Manager“, ir „Traefik“,
  nesusiejant bazinio Compose failo su vienu produktu.
- Leidimo žymos skelbia bendrą AMD64 ir ARM64 platformoms skirtą GHCR programos
  atvaizdą.

### Pakeista

- Esami vaikų profiliai ir PIN po atnaujinimo išlieka, tačiau kiekvieną vaiko
  naršyklę arba PWA reikia vieną kartą susieti. Senos vaikų „Web Push“
  prenumeratos pašalinamos ir susietame įrenginyje turi būti įjungtos iš naujo.
- Vidinis atsiliepimas aiškiai įvardytas kaip privatus šeimos pranešimas, o
  programos klaidoms pateikiama GitHub Issues nuoroda su įspėjimu nesiųsti
  šeimos duomenų.
- Diegimas ir atnaujinimas patikrina rašomų serverio katalogų UID/GID nuosavybę
  bei parsiunčia versijuotą programos atvaizdą.
- Periodinė priežiūra taip pat išvalo pasenusius saugumo skaitiklius, susiejimo
  nuorodas ir sesijas.

### Saugumas

- Tėvų prisijungimo, slaptažodžio atkūrimo ir vaikų PIN bandymai ribojami
  serverio duomenų bazėje saugomais skaitikliais.
- Persiųstos kliento IP antraštės priimamos tik iš nustatytų patikimų proxy, o
  pasirenkamas tinklo leidžiamų adresų sąrašas naudoja taip patikrintą adresą.
- Vaikų „Web Push“ prenumeratos susiejamos su patvirtintu įrenginiu, susiejimo
  nuorodos yra vienkartinės ir trumpalaikės, o įrenginių paslaptys duomenų
  bazėje saugomos maišos pavidalu.
- „Django“ administravimo maršrutas produkcijoje pagal nutylėjimą išjungtas.
- Regresijos testas patikrina, kad sugeneruotas VAPID privatus raktas yra
  realiai naudojamas EC privatus raktas.

## [26.3.2] - 2026-07-31

### Pakeista

- Nustatymuose naudojami trumpesni skilčių, laukų ir išsaugojimo veiksmų
  pavadinimai lietuvių ir anglų kalbomis.
- Programos poraštėje pridėta nuoroda į „KinKudos“ GitHub repozitoriją.

### Pataisyta

- Bendras šeimos ir atskirų vaikų loterijos žymimieji langeliai išlaiko vienodą
  kompaktišką dydį ir tinkamai lygiuojami kompiuterio bei mobiliajame vaizde.
- Vaikų kortelėse suvienodinta kredito limito ir savaitės loterijos būsenos
  skyryba, o kredito limito informacinė ikona pristumta arčiau pavadinimo.

## [26.3.1] - 2026-07-31

### Pakeista

- Tėvai gali nustatyti loterijos bilieto kainą ir vienam vaikui taikomą
  savaitės pirkimų limitą, išjungti loteriją visai šeimai arba konkrečiam
  vaikui. Bendras šeimos jungiklis turi viršenybę, o jau pradėtą bilietą vis
  tiek galima užbaigti.

### Pataisyta

- Darbų ir prizų katalogų pavadinimams bei tėvų veiksmų dialogų paaiškinimams
  nuosekliai naudojamas bendras sąsajos šriftas.
- Tėvų vaikų kortelėse rodomas likusių savaitės loterijos bilietų skaičius ir
  sumažintas tarpas po kredito limitu.
- Sutrumpintas lietuviškas atsiliepimų el. pašto adreso pavadinimas.

## [26.3.0] - 2026-07-30

### Pridėta

- Vaikas už 15 uždirbtų taškų gali pirkti prie temos pritaikytą nutrinamą
  loterijos bilietą, atidengti sidabrinę 3×3 skaičių lentelę ir gauti vieną
  sutampantį teigiamą, neigiamą arba tuščią rezultatą. Bilietas išlieka iki
  užbaigimo, per pirmadienio–sekmadienio savaitę galima pirkti ne daugiau kaip
  tris, o praradimas niekada neperžengia vaiko kredito ribos.
- Bent 50 taškų turintis ir tą savaitę bilieto nepirkęs vaikas su aktyviais
  pranešimais gali gauti vieną aiškiai riziką nurodantį priminimą atsitiktiniu
  saugiu laiku antroje savaitės pusėje.
- Tėvai mato nekeičiamą savaitės bilietų būseną ir atskirus bilieto kainos bei
  galutinio rezultato apskaitos įrašus, tačiau sisteminio prizo nevaldo.

## [26.2.2] - 2026-07-30

### Pakeista

- Tėvų katalogų skiltys dabar rikiuojamos vertikaliai, darbų pavadinimai
  naudoja bendrą sistemos šriftą, o nustatymuose naudojami didesni laukų
  pavadinimai ir palikti tik pavadinti grupių skirtukai.
- Vaiko greitieji veiksmai turi aiškesnes ikonas ir rikiuojami tokia tvarka:
  „Atliktas darbas“, „Skirti nuobaudą“, „Paskirti darbus šiandienai“,
  „Koreguoti taškus“ ir „Keisti kreditą“.
- Tėvų veiksmų istorijoje rodoma ne daugiau kaip 50 paskutinių septynių dienų
  veiksmų, išsaugant nekintamus apskaitos įrašus.
- Naujausių atsarginių kopijų veiksmų sąraše rodoma ne daugiau kaip penki
  įrašai.
- Sutrumpinti taškų už darbo nuotrauką ir saugomų atsiliepimų nuotraukų
  nustatymų pavadinimai.

### Pataisyta

- Išsaugojus bendruosius šeimos nustatymus vėl atveriama nustatymų, o ne
  pradžios skiltis.
- Kredito limito informacinė ikona centruojama su jo pavadinimu.

## [26.2.1] - 2026-07-30

### Pataisyta

- Atliktų, atšauktų ir nebegaliojančių paskirtų darbų siuntų istorijoje
  neberodomas klaidinantis veiksmas „Atšaukti likusius“.

## [26.2.0] - 2026-07-30

### Pridėta

- Tėvai nauju penktuoju greituoju veiksmu gali vaikui paskirti šiandienos
  katalogo darbų sąrašą ir vieną individualų darbą. Darbų reikšmės
  užfiksuojamos, vidurnaktį jie nebegalioja, juos galima atšaukti, o istorija
  išlieka tėvų erdvėje.
- Vaikas visose septyniose temose paskirtus darbus mato kaip svarbiausią
  sąrašą ir kiekvieną pažymėjęs atliktu taškus gauna iškart.
- Tėvai pasirinktinai gali blokuoti naujus prizų prašymus, kol bus atlikti
  visi galiojantys paskirti darbai; esami prašymai ir kiti vaiko veiksmai
  lieka pasiekiami.
- Apie naujai paskirtus darbus vaiko įrenginiams siunčiamas prie temos
  pritaikytas „Web Push“ pranešimas.

### Pakeista

- Katalogo darbo negalima paskirti, kol jis laukia patvirtinimo, jau yra
  paskirtas arba tam vaikui šiandien jau buvo užskaitytas.

## [26.1.7] - 2026-07-30

### Pataisyta

- Šeimos nustatymuose naudojamos kompaktiškos etiketės, lauko ir paaiškinimo
  eilutės, derančios su el. pašto bei kopijų suvestinėmis; paaiškinimai
  tinkamai sumažinti, o mobiliajame ekrane eilutės persirikiuoja į vieną
  stulpelį.

## [26.1.6] - 2026-07-30

### Pakeista

- Formų etiketėms, pagalbiniam tekstui, laukų užpildams, sekcijų skirtukams ir
  laukų tipografikai pritaikyta aiškesnė bei nuoseklesnė vaizdinė hierarchija.
- Tėvų ir vaikų paskyrų kūrimo veiksmų tekstai sutrumpinti.
- El. pašto ir kopijų suvestinėse prislopinti pavadinimai atskirti nuo
  paryškintų reikšmių, o sąrašai pritaikyti siauram ekranui.

### Pataisyta

- Prizų patvirtinimo veiksmuose naudojamos tokios pačios patvirtinimo ir
  atmetimo ikonos kaip darbų patvirtinime.
- Siaurame ekrane tėvų ir vaikų veiksmų istorijos taškų reikšmės lygiuojamos su
  būsenos bei nuotraukos valdikliais.

## [26.1.5] - 2026-07-30

### Pataisyta

- Kopijų agentas aktyvią SQLite duomenų bazę atidaro aiškiu `mode=ro` ir
  `query_only` režimu, o duomenų katalogo prijungimas leidžia SQLite valdyti
  saugiai internetinei kopijai reikalingus užrakinimo bei WAL failus.
- Vietinės duomenų bazės atidarymo ir kopijos failo sukūrimo klaidos dabar
  atskiriamos aiškesniais diagnostiniais pranešimais.

## [26.1.4] - 2026-07-30

### Pataisyta

- Leidimo atnaujintojas po sėkmingos būklės patikros atnaujina versijuojamus
  `deploy` valdymo scenarijus. Tai pašalina serveryje galėjusį likti seną
  `backup.sh`, kuris kvietė nebeegzistuojantį `restic` servisą.
- Atnaujinant ir toliau neliečiami vietinis `deploy/.env`, šeimos duomenys,
  kopijos bei paslaptys.

## [26.1.3] - 2026-07-30

### Pakeista

- Tėvų, pradžios ir bendroje sistemos sąsajoje naudojama dokumentuota anglies,
  pagalbinė pilka, kreminė, slyvų, šalavijo, gintarinė ir švelniai raudona
  paletė bei vienoda laukų ir paaiškinimų tipografika.
- El. pašto ir kopijų konfigūracijos suvestinės pateikiamos kompaktiškais
  sąrašais įprastu raidžių registru, sutrumpinti nustatymų veiksmai ir
  suvienodintas mygtukų lygiavimas.
- Lietuviškame ir angliškame README pašalintos dekoratyvinės ikonos bei
  ženkleliai, pridėtos nustatymų ir dviejų vaiko temų ekrano nuotraukos,
  pašalinta pasenusi „Orange Pi“ instrukcijos nuoroda.

### Pataisyta

- Nesukonfigūruotos kopijos būsena rodoma kaip „Neįjungta“, vykdoma kopija –
  kaip „Kopijuojama“ pagrindiniame indikatoriuje, o tvarkinga kopija – žalia
  būsena „Įjungta“, nekartojant atskiro progreso ženklelio.
- PWA temos ir fono metaduomenų spalvos suderintos su bendra sąsajos palete.

## [26.1.2] - 2026-07-30

### Pataisyta

- Kopijų agentui pridėtas atskiras išorinis Docker tinklas, leidžiantis
  pasiekti S3 saugyklą, kartu išlaikant atskirą vidinį ryšį su programa.
- Kopijų diagnostikos komandos dabar aiškiai nurodo `deploy/compose.yml`, todėl
  veikia paleistos iš diegimo šakninio katalogo.

## [26.1.1] - 2026-07-30

### Pakeista

- „Nustatymuose“ palikta viena aiški antraščių hierarchija, centruoti skirtukai,
  atskirta laukų tipografika, stilizuoti pasirinkimo laukai, pagrindinio
  stiliaus veiksmų mygtukai ir vienodos žalios / raudonos tarnybų būsenos.
- Projekto README dabar patraukliau pateikia patikrintas galimybes, privatumo
  ribas, diegimo modelį ir išgalvotų demonstracinių duomenų ekrano nuotraukas.
- Kopijų dokumentacijoje atskirta neteisingo S3 hostname ir Docker ar serverio
  DNS klaida bei pridėtos tiesioginės diagnostikos komandos.

### Pataisyta

- Jautriuose nustatymuose prašoma „Jūsų paskyros slaptažodžio“ vietoje ilgesnio
  paskyros tipą kartojančio teksto.
- Veiksmų istorijos filtre prie savaime aiškaus pasirinkimo nebekartojamas
  atskiras užrašas „Vaikas“.
- Regresinis testas užtikrina, kad `service-worker.js` visada būtų pateikiamas
  su `Cache-Control: no-cache`.

## [26.1.0] - 2026-07-30

### Pridėta

- Tėvų administratorius „Nustatymuose“ gali patikrinti ir pakeisti SMTP
  nustatymus; SMTP slaptažodis lieka tik lokaliame ribotų teisių paslapčių
  faile.
- Bendruosiuose šeimos nustatymuose galima pakeisti šeimos pavadinimą.

### Pakeista

- Nustatymai logiškai suskirstyti į šeimos, vaikų ir taškų, privatumo,
  el. pašto, kopijų, paskyrų bei atsiliepimų blokus.
- Septintoji vaiko tema pervadinta į originalią „Blockville“ temą su kubelių
  valiuta ir su trečiųjų šalių ženklais nesusietais sąsajos tekstais.

### Pataisyta

- Tikrinant kopijų saugyklą pakartojamas bandymas po laikinos „Docker“ DNS
  klaidos, o techninis resolverio tekstas pakeistas aiškiu patarimu patikrinti
  S3 adresą.
- Darbų, nuobaudų ir prizų redagavimo formose po laukų pavadinimų visur rodomi
  dvitaškiai.

### Saugumas

- Keičiant jautrius SMTP ar kopijų prisijungimo duomenis būtinas pakeitimą
  atliekančio tėvų administratoriaus slaptažodis. Paskyrų redagavimui paliktos
  esamos autentifikavimo taisyklės.

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

- „Blockville Pasaulis“ tapo septintąja vaiko tema: pridėta tamsi žaidimo
  sąsaja, kubelių linksniai, iššūkių ir prizų tekstai, paspaudžiami
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
