# Tėvų nustatymai

Kelias: **Tėvai → Nustatymai**. Čia yra šeimos taisyklės, įrenginiai, paskyros, pasirenkamas saugumas, el. paštas, kopijos ir šeimos atsiliepimai. Pradėkite nuo **Šeimos nustatymų**; tik administratoriui skirtas paslaugas palikite vėlesniam laikui, kol neveikia pagrindinis šeimos ciklas.

> **Kas gali ką keisti?** Visi tėvai gali naudoti įprastus šeimos nustatymus ir tvarkyti paskyras. Tėvų administratorius (paprastai pirmas diegimo metu sukurtas tėvas) vienintelis gali keisti tinklo prieigą, SMTP, atsarginių kopijų duomenis, paleisti kopiją ir atšaukti visus vaikų įrenginius.

![Angliški tėvų nustatymai](../assets/parent-settings-2026.png)

Ekrano nuotraukoje naudojami tik išgalvoti demonstraciniai duomenys.

## 1. Šeimos nustatymai

Pirmas blokas valdo visai šeimai bendras taisykles. Nauja reikšmė taikoma būsimiems veiksmams; ji nekeičia jau užbaigto darbo, patvirtinto prizo ar esamo istorijos įrašo.

### Šeimos pavadinimas

| Laukelis | Reikšmė | Kas pasikeičia |
| --- | --- | --- |
| **Šeimos pavadinimas** | Vardas, rodomas šeimai skirtose antraštėse ir žinutėse. | Keičiamas tik rodomas pavadinimas, o ne naudotojų vardai, domenas ar prieiga. |

### Privilegijos

| Laukelis | Reikšmė | Kas pasikeičia |
| --- | --- | --- |
| **Taškai už darbo nuotrauką** | Papildomi taškai, kai vaikas pateikia darbą su nuotrauka. `0` išjungia priedą. | Reikšmė užfiksuojama darbo pateikimo metu; vėliau redagavimas nekeičia jau laukiančio ar patvirtinto darbo. |
| **Gimtadienio taškai** | Kasmetinė dovana kiekvienam vaikui jo išsaugotą gimtadienį. `0` išjungia. | Nauja reikšmė taikoma būsimiems apdovanojimams; tam pačiam vaikui tais pačiais metais dovana neskiriama du kartus. |
| **Įjungti loterijos bilietus** | Bendras pasirenkamos nutrinamos loterijos jungiklis. | Išjungus neleidžiami nauji pirkimai ir priminimai, tačiau pradėtą bilietą galima baigti. Kiekvienas vaikas turi ir savo jungiklį. |
| **Loterijos bilieto kaina** | Kiek taškų kainuos būsimas bilietas. | Nauja kaina taikoma tik būsimiems pirkimams; jau nupirktas bilietas išlaiko užfiksuotą kainą. |
| **Savaitinis bilietų limitas** | Kiek bilietų vienas vaikas gali pirkti nuo pirmadienio iki sekmadienio. | Nauja riba taikoma būsimiems pirkimams; skaitiklis atsinaujina kiekvieną pirmadienį. |

### Saugojimas

Šie laukai valdo automatinį įkeltų vaizdų šalinimą, o ne paskyrų ar taškų istorijos trynimą.

| Laukelis | Reikšmė | Kas pasikeičia |
| --- | --- | --- |
| **Saugoti darbų nuotraukas** | Kiek laiko saugomos užbaigtų darbų nuotraukos: neribotai, 7, 30 arba 90 dienų. | Laukiančių arba taisyti grąžintų darbų nuotraukos automatiškai netrinamos. |
| **Saugoti atsiliepimų nuotraukas** | Kiek laiko saugoma išspręsto atsiliepimo ekrano nuotrauka. | Neišspręstų atsiliepimų nuotraukos automatiškai netrinamos. |

## 2. Vaikų įrenginiai

Tik susietas įrenginys gali rodyti vaikų profilius arba priimti vaiko PIN. Profilis saugo vardą, taisykles ir istoriją, o įrenginys yra naršyklė, telefonas, planšetė ar PWA, kuriam leista juo naudotis.

| Valdiklis | Kada naudoti | Rezultatas |
| --- | --- | --- |
| **Įrenginio pavadinimas** | Kai susiejate dabartinį kompiuterį ar planšetę. | Suteikia aiškų pavadinimą, pvz., „Virtuvės planšetė“. |
| **Leisti vaikams naudoti šį įrenginį** | Kai esate prie vaiko įrenginio. | Iškart susieja šią naršyklę/PWA. Tuomet galima pasirinkti vaiką ir įvesti PIN. |
| **Sukurti privačią susiejimo nuorodą** | Kai reikia susieti kitą telefoną, planšetę ar naršyklę. | Sukuria vienkartinę nuorodą, galiojančią **10 minučių**; ją atidarykite tik numatytame įrenginyje. |
| **Pervadinti** | Kai sąrašas neaiškus. | Keičia tik pavadinimą, prieigos nenutraukia. |
| **Atšaukti** | Pametus, pardavus ar nebe šeimos valdomam įrenginiui. | Panaikina vaiko prieigą ir pranešimus tame įrenginyje; norint grįžti reikės susieti iš naujo. |
| **Atšaukti visus vaikų įrenginius** | Esant platesniam saugumo incidentui. | Tik administratoriui; reikia jo slaptažodžio ir visus įrenginius teks susieti iš naujo. |

## 3. Tinklo prieiga

Tai **pasirenkamas papildomas saugumo sluoksnis**, o ne privalomas pirmas žingsnis. Tėvų slaptažodžiai, vaikų PIN ir įrenginių susiejimas veikia ir tuomet, kai ribojimas išjungtas.

| Režimas | Ką leidžia | Kada tinka |
| --- | --- | --- |
| **Prieiga iš interneto** | Jokio IP ribojimo. | Įprastas pasirinkimas daugumai šeimų. |
| **Riboti vaikų prieigą** | Vaikų puslapiai veikia tik iš įrašytų IP adresų ar tinklų; tėvų puslapiai IP neribojami. | Vaikai KinKudos turi naudoti tik namuose, o tėvai keliauja. |
| **Riboti visą prieigą** | Vaikų ir tėvų puslapiai veikia tik iš įrašytų adresų. | Tik žinomam stabiliam namų/VPN tinklui ir administratoriui, mokančiam atkurti prieigą. |

Į **Leidžiamus IP adresus ir tinklus** rašykite po vieną IPv4, IPv6 ar CIDR tinklą eilutėje, pvz. `192.0.2.25`, `192.0.2.0/24` arba `2001:db8::/64`. Prieš **Riboti visą prieigą** įrašykite formoje rodomą dabartinį IP. Netinkama taisyklė gali užrakinti visus; tuomet reikės serverio administratoriaus.

## 4. El. pašto nustatymai (SMTP)

SMTP neprivalomas. Jis reikalingas tėvų slaptažodžio atkūrimui ir, nustačius gavėją, privačių atsiliepimų el. pašto pranešimams. Pats atsiliepimas KinKudos išsaugomas ir išjungus el. paštą.

| Laukelis | Ką įrašyti | Pastaba |
| --- | --- | --- |
| **Įjungti el. paštą** | Įjunkite arba išjunkite laiškų siuntimą. | Išjungimas netrina atsiliepimų. |
| **SMTP serveris** | El. pašto tiekėjo siunčiamų laiškų serverio vardą. | Pvz. `smtp.example.com`, be URL kelio. |
| **SMTP prievadas** | Tiekėjo nurodytą prievadą. | Dažniausiai 587 STARTTLS arba 465 SSL/TLS; vadovaukitės tiekėju. |
| **Šifravimas** | `STARTTLS`, `SSL/TLS` arba `None`. | `None` rinkitės tik patikimam vidiniam pašto relay. |
| **SMTP naudotojo vardas** | Tiekėjo prisijungimo vardą. | Dažnai el. pašto adresas, bet ne visada. |
| **SMTP slaptažodis** | Pašto paslaugos slaptažodį ar programėlės slaptažodį. | Po išsaugojimo nerodomas; įveskite kiekvieną kartą keisdami nustatymus. |
| **Siuntėjo el. pašto adresas** | Adresą, kurį matys gavėjai. | Paprastai turi būti leidžiamas SMTP tiekėjo. |
| **Atsiliepimų gavėjo el. paštas** | Adresą, kuriuo ateis papildomi atsiliepimų pranešimai. | Pranešimas išlieka privatus programoje. |
| **Jūsų paskyros slaptažodis** | Administratorius įveda savo dabartinį slaptažodį. | Apsaugo jautrią konfigūraciją atidarytoje sesijoje. |

KinKudos prieš išsaugodamas patikrina SMTP ryšį. SMTP slaptažodis niekada nerodomas.

## 5. Atsarginės kopijos

Kopijos neprivalomos, bet labai rekomenduojamos šeimai pradėjus naudoti KinKudos. Sistema kasdien sukuria šifruotą nuotolinę duomenų bazės ir įkeltų nuotraukų kopiją. Atkūrimas sąmoningai nėra mygtukas internete – tai serverio administratoriaus veiksmas.

| Rodmuo | Reikšmė |
| --- | --- |
| **Įjungta** (žalia) | Saugykla nustatyta, o paskutinė sėkminga kopija ne senesnė kaip 7 dienos. |
| **Kopijuojama** (gintarinė) | Vyksta kopija; vienu metu gali veikti tik viena. |
| **Neįjungta** | Nuotolinė saugykla dar nesukonfigūruota. |
| **Reikia dėmesio** (raudona) | Paslauga nepasiekiama, kopija pasenusi arba pateikta klaida. Pirmiausia perskaitykite klaidą. |

**Kurti kopiją dabar** paprašo papildomos kopijos; ji niekada neatkuria duomenų.

| Laukelis | Ką įrašyti |
| --- | --- |
| **Saugyklos tiekėjas** | „Backblaze B2“ (rekomenduojama) arba kitas su S3 suderinamas tiekėjas. |
| **S3 endpoint** | Tiekėjo S3 API hostą be `https://` ir be galinio `/`. |
| **Bucket pavadinimas** | Atskirtą KinKudos kopijoms skirtą bucket, be kelio. |
| **Regionas** | Tiekėjo regioną, jei jis reikalingas. |
| **Application key ID / Application key** | Ribotų teisių prisijungimo duomenis, geriausia tik šiam bucket. |
| **Jūsų paskyros slaptažodis** | Dabartinį administratoriaus slaptažodį. |

Ryšys tikrinamas prieš išsaugojimą, o prisijungimo duomenys saugomi atskiruose apsaugotuose serverio failuose. Žalia būsena naudinga, tačiau pilnas saugumo patikrinimas – bandomasis atkūrimas saugioje atskiroje vietoje ir repo slaptažodžio saugojimas ne serveryje.

## 6. Šeimos paskyros ir programos nustatymai

**Nauja tėvų paskyra** sukuria atskirą suaugusiojo naudotojo vardą, el. paštą ir stiprų slaptažodį. **Naujas vaiko profilis** nustato vardą, pasirenkamą kreipinį lietuvių kalbai, pradinį PIN, kredito limitą, loterijos leidimą ir gimtadienį.

Skiltyje **Tėvų paskyros** galima keisti naudotojo vardą, el. paštą ir slaptažodį. Palikus naujo slaptažodžio laukelius tuščius, senas slaptažodis išlieka. Paskyros atšaukimas ją išjungia, o istorija lieka; paskutinio aktyvaus tėvo išjungti negalima.

Skiltyje **Vaikų profiliai** galima keisti vardą, kreditą, individualų loterijos jungiklį, gimtadienį ir PIN. Kreditas yra žemiausias leidžiamas balansas, pvz., `-100`; bendra šeimos loterija taip pat turi būti įjungta. Vaiko gimtadienio prašymas reikalauja tėvų sprendimo, bet tėvai datą gali redaguoti tiesiogiai. Palikite naują PIN tuščią, jei jo keisti nenorite. Vaiko profilio atšaukimas išsaugo jo istoriją.

## 7. Šeimos atsiliepimai

Tėvai ir vaikai gali programoje išsaugoti privatų **pasiūlymą** arba **problemos** pranešimą su pasirenkama ekrano nuotrauka. Naudokite **Tipas** ir **Būsena** filtrus. **Naujas** reiškia dar neperžiūrėtą, **Peržiūrėtas** – tėvai perskaitė, **Planuojamas** – šeima ketina imtis veiksmų, o **Išspręstas** – papildomų veiksmų nebesitikima. Atidarykite įrašą, peržiūrėkite nuotrauką ir išsaugokite būseną.

Kad pranešimas būtų naudingas, KinKudos taip pat išsaugo pateikusiojo vaidmenį ir vardą, puslapio kelią, programos versiją, kalbą, pasirinktą temą ir naršyklės/įrenginio aprašą. Ši informacija lieka šeimos instaliacijoje ir į „GitHub“ nesiunčiama. Nuotraukoms taikoma aukščiau nurodyta saugojimo taisyklė.

## Nuotraukų ribos ir laiko taisyklės

Darbų įrodymai ir atsiliepimų ekrano nuotraukos priima JPEG, PNG, WebP, HEIC arba HEIF iki **12 MB**. Avatarai priima tuos pačius formatus iki **5 MB** ir apkerpami į kvadratą. Nuotraukos apdorojamos privačiam saugojimui; nekelkite daugiau šeimos informacijos nei reikia darbui ar problemai paaiškinti.

Paskirti dienos darbai baigiasi vidurnaktį pagal **vietinį serverio laiką**. Loterijos limitai atsinaujina kiekvieną pirmadienį tame pačiame kalendoriniame kontekste. Jei šeima gyvena kitoje laiko juostoje nei serveris, prieš remdamiesi vidurnakčio taisykle susitarkite, pagal kurį laiką gyvena dienos darbai.

Pakartojamai viešai programos klaidai naudokite [GitHub Issues](https://github.com/VooZ2/kinkudos/issues), tačiau niekada nekelkite šeimos duomenų.

[Tinklo prieiga →](../security/network-access.lt.md) · [Atsarginės kopijos →](../security/backups.lt.md) · [English](settings.md)
